"""
yd_analytics.assist — Capa de "entendimiento": pregunta en lenguaje natural →
MetricQuery + gráfico sugerido.

Dos modos:
- **Con LLM** (opcional): se le pasa un callable `llm(prompt) -> dict`; el módulo
  arma el prompt con el registro y valida la salida contra el contrato.
- **Sin LLM** (por defecto): un emparejador por reglas, determinista y offline, que
  puntúa métricas por solape de palabras y detecta dimensiones/forma en la pregunta.

El resolver sigue eligiendo el gráfico final; aquí solo se traduce la intención a
una consulta. La IA no reemplaza las reglas: las alimenta.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Callable

from . import registry
from .schemas import MetricQuery, MetricSpec


@dataclass
class Suggestion:
    query: MetricQuery
    chart_hint: str | None
    rationale: str
    confidence: float


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]", " ", s.lower())


def _tokens(s: str) -> set[str]:
    return {t for t in _norm(s).split() if len(t) > 2}


# pistas de forma → chart_hint
_HINTS = [
    (re.compile(r"distribuc|histograma|rango"), "histogram"),
    (re.compile(r"composic|proporcion|parte|reparto"), "pie"),
    (re.compile(r"tendenc|evoluc|en el tiempo|por (mes|ano|periodo)|serie"), "line"),
    (re.compile(r"correlac|relacion entre|vs\.?|contra"), "scatter"),
    (re.compile(r"comparar|por [a-z]"), "bar"),
]
_TEMPORAL_HINT = re.compile(r"tendenc|evoluc|en el tiempo|serie|por (mes|ano|periodo)")


def _all_specs() -> list[MetricSpec]:
    return [registry.get(i) for i in registry.all_ids()]


def interpret(question: str, specs: list[MetricSpec] | None = None, *,
              llm: Callable[[str], dict] | None = None) -> Suggestion:
    specs = specs or _all_specs()

    if llm is not None:
        raw = llm(_build_prompt(question, specs))
        q = MetricQuery(metric=raw["metric"], dimensions=raw.get("dimensions", []),
                        chart_hint=raw.get("chart_hint"))
        return Suggestion(q, raw.get("chart_hint"), raw.get("rationale", "LLM"), 0.9)

    # --- Fallback por reglas (sin LLM) --- #
    qtok = _tokens(question)

    def score(sp: MetricSpec) -> int:
        base = _tokens(f"{sp.titulo} {sp.descripcion} {sp.id}")
        return len(qtok & base)

    best = max(specs, key=score)
    conf = min(0.85, 0.35 + 0.15 * score(best))

    # dimensiones mencionadas (entre las permitidas por la métrica)
    dims = [d for d in best.grano if _norm(d) in _norm(question)]
    if best.dim_temporal and _TEMPORAL_HINT.search(_norm(question)) and best.dim_temporal not in dims:
        dims = [best.dim_temporal] + [d for d in dims if d != best.dim_temporal]

    hint = next((h for rx, h in _HINTS if rx.search(_norm(question))), None)

    rationale = (f"Coincidencia con «{best.titulo}»"
                 + (f", desglose por {', '.join(dims)}" if dims else "")
                 + (f", forma sugerida {hint}" if hint else "") + ".")
    return Suggestion(MetricQuery(metric=best.id, dimensions=dims, chart_hint=hint),
                      hint, rationale, conf)


def openai_compatible_llm(base_url: str, api_key: str, model: str,
                          *, temperature: float = 0.0, timeout: float = 20.0):
    """Adaptador para cualquier API compatible con OpenAI → callable usable como `llm`.

    Sirve para **Cerebras** (el de Áncora), **Kimi/Moonshot** y OpenAI: solo cambian
    base_url y model. Sin dependencias extra (usa la stdlib). Pide salida JSON.

        llm = openai_compatible_llm("https://api.cerebras.ai/v1", KEY, "llama-3.3-70b")
        # Kimi:  openai_compatible_llm("https://api.moonshot.ai/v1", KEY, "kimi-k2-...")
        sug = interpret("riesgo por carrera", llm=llm)
    """
    import json
    import urllib.request

    def _call(prompt: str) -> dict:
        body = json.dumps({
            "model": model, "temperature": temperature,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": "Responde SOLO JSON válido."},
                {"role": "user", "content": prompt},
            ],
        }).encode()
        req = urllib.request.Request(
            base_url.rstrip("/") + "/chat/completions", data=body,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
        return json.loads(data["choices"][0]["message"]["content"])

    return _call


def _build_prompt(question: str, specs: list[MetricSpec]) -> str:
    catalogo = "\n".join(f"- {s.id}: {s.titulo}. dims={s.grano} temporal={s.dim_temporal}" for s in specs)
    return (
        "Traduce la pregunta a una consulta de métrica. Responde SOLO JSON con "
        "{metric, dimensions[], chart_hint?, rationale}. La métrica y las dimensiones "
        "DEBEN salir del catálogo.\n\nCatálogo:\n" + catalogo + f"\n\nPregunta: {question}\n"
    )
