"""
yd_analytics.report — Informe en HTML con RESÚMENES de cada gráfico.

Toma un conjunto de paneles (título + forma + filas), calcula estadística real
con `stats`, y redacta un resumen en lenguaje natural **determinista**: cada frase
se arma a partir de los números calculados (nunca inventados por un LLM). Devuelve
un HTML autocontenido con la marca de la casa: resumen ejecutivo, un gráfico por
panel (SVG), tarjetas de estadísticos y hallazgos + cautelas.

Uso:
    from yd_analytics import report
    html = report.build_report(paneles, titulo="Informe — <dataset>")
"""
from __future__ import annotations

from typing import Any

from . import stats as S

# Paleta de la casa (validada; sin violeta).
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#e34948"]


# --------------------------------------------------------------------------- #
#  Formato es-EC
# --------------------------------------------------------------------------- #

def fmt(x: Any, dec: int = 1) -> str:
    """Número con separador de miles '.' y decimal ',' (es-EC)."""
    if x is None:
        return "—"
    try:
        s = f"{float(x):,.{dec}f}"
    except (TypeError, ValueError):
        return str(x)
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def pct(x: Any, dec: int = 1) -> str:
    return "—" if x is None else f"{fmt(x, dec)}%"


def signed(x: Any, dec: int = 1) -> str:
    if x is None:
        return "—"
    return ("+" if float(x) >= 0 else "") + fmt(x, dec)


# --------------------------------------------------------------------------- #
#  Narrativa determinista por forma
# --------------------------------------------------------------------------- #

def narrate(block: dict, titulo: str = "") -> dict:
    """Devuelve {resumen:[frases], cautelas:[...], kpis:[{label,valor}]}."""
    shape = block.get("shape")
    frases: list[str] = []
    kpis: list[dict] = []
    d = block.get("descriptivos") or {}

    if shape == "timeseries":
        t = block.get("tendencia") or {}
        if t.get("n"):
            frases.append(
                f"La serie va de {fmt(t.get('primero'))} a {fmt(t.get('ultimo'))} "
                f"en {t.get('n')} períodos, con tendencia {t.get('direccion','')}.")
            if t.get("p") is not None:
                frases.append(
                    f"La pendiente es {signed(t.get('pendiente'),2)} por período "
                    f"(R²={fmt(t.get('r2'),2)}, p={fmt(t.get('p'),3)}); "
                    f"Mann-Kendall: {t.get('mann_kendall',{}).get('tendencia','—')} "
                    f"(p={fmt(t.get('mann_kendall',{}).get('p'),3)}).")
            if t.get("cambio_total_pct") is not None:
                frases.append(f"Cambio acumulado: {signed(t.get('cambio_total_pct'))}% "
                              f"(último período {signed(t.get('cambio_ultimo_pct'))}%).")
            rng = t.get("pronostico_rango") or [None, None]
            frases.append(f"Pronóstico del próximo período: {fmt(t.get('pronostico_siguiente'))} "
                          f"(rango {fmt(rng[0])}–{fmt(rng[1])} al 95%).")
            kpis = [
                {"label": "Tendencia", "valor": t.get("direccion", "—")},
                {"label": "Cambio total", "valor": pct(t.get("cambio_total_pct"))},
                {"label": "R²", "valor": fmt(t.get("r2"), 2)},
                {"label": "Pronóstico", "valor": fmt(t.get("pronostico_siguiente"))},
            ]

    elif shape == "category":
        c = block.get("categorico") or {}
        lid = c.get("lider") or {}
        if c.get("k"):
            frases.append(
                f"{c.get('k')} categorías, total {fmt(c.get('total'))}. "
                f"Lidera «{lid.get('label','—')}» con {pct(lid.get('share_pct'))} del total.")
            chi = c.get("chi2_uniformidad")
            if chi:
                frases.append(
                    f"El reparto {'es' if chi.get('uniforme') else 'NO es'} uniforme "
                    f"(χ²={fmt(chi.get('chi2'),2)}, p={fmt(chi.get('p'),3)}); "
                    f"concentración {c.get('concentracion','—')} "
                    f"(HHI normalizado {fmt(c.get('hhi_norm'),2)}, Gini {fmt(c.get('gini'),2)}).")
            if d.get("n"):
                frases.append(f"Por categoría: media {fmt(d.get('media'))}, "
                              f"mediana {fmt(d.get('mediana'))}, rango {fmt(d.get('min'))}–{fmt(d.get('max'))}.")
            o = block.get("atipicos", {}).get("iqr", {})
            if o.get("n"):
                frases.append(f"Atípicos (IQR): {o.get('n')} categoría(s) fuera del rango típico.")
            kpis = [
                {"label": "Líder", "valor": lid.get("label", "—")},
                {"label": "Participación", "valor": pct(lid.get("share_pct"))},
                {"label": "Categorías", "valor": fmt(c.get("k"), 0)},
                {"label": "Concentración", "valor": c.get("concentracion", "—")},
            ]

    elif shape in ("correlation", "distribution"):
        cor = block.get("correlacion")
        if cor and cor.get("n"):
            frases.append(
                f"Correlación {cor.get('fuerza','')} {cor.get('direccion','')}: "
                f"Pearson r={fmt(cor.get('pearson_r'),2)} (p={fmt(cor.get('pearson_p'),3)}), "
                f"Spearman ρ={fmt(cor.get('spearman_rho'),2)}. "
                f"{'Significativa' if cor.get('significativa') else 'No significativa'} al 95%.")
            kpis = [
                {"label": "Pearson r", "valor": fmt(cor.get("pearson_r"), 2)},
                {"label": "R²", "valor": fmt(cor.get("pearson_r2"), 2)},
                {"label": "Spearman ρ", "valor": fmt(cor.get("spearman_rho"), 2)},
                {"label": "Fuerza", "valor": cor.get("fuerza", "—")},
            ]
        if d.get("n"):
            nrm = block.get("normalidad") or {}
            frases.append(
                f"Distribución {d.get('forma','')}; media {fmt(d.get('media'))} vs. "
                f"mediana {fmt(d.get('mediana'))} (brecha {signed(d.get('brecha_media_mediana'),2)}).")
            if nrm.get("prueba"):
                frases.append(f"Normalidad ({nrm['prueba']}): "
                              f"{'sí' if nrm.get('es_normal') else 'no'} (p={fmt(nrm.get('p'),3)}).")

    elif shape == "proportion":
        pr = block.get("proporcion") or {}
        if pr.get("n"):
            wl = pr.get("wilson") or [None, None]
            frases.append(
                f"Estimación: {pct(pr.get('p', 0) * 100)} "
                f"(±{pct(pr.get('margen_error_pct'))} al {int(pr.get('conf', .95) * 100)}%), "
                f"sobre n={fmt(pr.get('n'), 0)}"
                + (f" de un universo de {fmt(pr.get('poblacion'), 0)}" if pr.get("poblacion") else "") + ".")
            frases.append(f"Intervalo de confianza (Wilson): "
                          f"{pct(wl[0] * 100)} – {pct(wl[1] * 100)}.")
            frases.append("El margen de error es la mitad del ancho del intervalo; "
                          "un traslape entre dos candidatos significa empate técnico.")
            kpis = [
                {"label": "Estimación", "valor": pct(pr.get("p", 0) * 100)},
                {"label": "Margen de error", "valor": "±" + pct(pr.get("margen_error_pct"))},
                {"label": "IC 95% (Wilson)", "valor": f"{fmt(wl[0]*100)}–{fmt(wl[1]*100)}%"},
                {"label": "Muestra", "valor": fmt(pr.get("n"), 0)},
            ]

    elif shape == "scalar":
        frases.append(f"Valor: {fmt(block.get('valor'))}.")
        kpis = [{"label": titulo or "Valor", "valor": fmt(block.get("valor"))}]

    # Descriptivos como KPIs de respaldo si no hubo forma específica.
    if not kpis and d.get("n"):
        kpis = [
            {"label": "n", "valor": fmt(d.get("n"), 0)},
            {"label": "Media", "valor": fmt(d.get("media"))},
            {"label": "Mediana", "valor": fmt(d.get("mediana"))},
            {"label": "Desv. est.", "valor": fmt(d.get("std"))},
        ]

    return {"resumen": frases, "cautelas": block.get("cautelas", []), "kpis": kpis}


# --------------------------------------------------------------------------- #
#  Gráficos SVG (deterministas, desde los datos)
# --------------------------------------------------------------------------- #

def _svg_bars(rows, lcol, vcol, top=8):
    data = [(str(r.get(lcol)), S._f(r.get(vcol)) or 0) for r in rows]
    data = [d for d in data if d[1] is not None][:top]
    if not data:
        return ""
    vmax = max(v for _, v in data) or 1
    h = 26 * len(data) + 10
    bars = []
    for i, (lab, v) in enumerate(data):
        w = 320 * (v / vmax)
        y = 8 + i * 26
        bars.append(
            f'<text x="0" y="{y+12}" font-size="12" fill="#52514e">{_esc(lab)[:22]}</text>'
            f'<rect x="150" y="{y+2}" width="{w:.1f}" height="14" rx="3" fill="{CAT[0]}"/>'
            f'<text x="{155+w:.1f}" y="{y+13}" font-size="11" fill="#52514e">{fmt(v)}</text>')
    return f'<svg viewBox="0 0 520 {h}" width="100%" height="{h}" role="img">{"".join(bars)}</svg>'


def _svg_line(rows, lcol, vcol):
    vals = [S._f(r.get(vcol)) for r in rows]
    vals = [v for v in vals if v is not None]
    if len(vals) < 2:
        return ""
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1
    W, H = 520, 180
    pts = []
    for i, v in enumerate(vals):
        x = 10 + i * (W - 20) / (len(vals) - 1)
        y = 10 + (H - 30) * (1 - (v - lo) / span)
        pts.append(f"{x:.1f},{y:.1f}")
    poly = " ".join(pts)
    area = f"10,{H-20} " + poly + f" {W-10},{H-20}"
    dots = "".join(f'<circle cx="{p.split(",")[0]}" cy="{p.split(",")[1]}" r="3" fill="{CAT[0]}"/>' for p in pts)
    return (f'<svg viewBox="0 0 {W} {H}" width="100%" height="{H}" role="img">'
            f'<polygon points="{area}" fill="rgba(42,120,214,.10)"/>'
            f'<polyline points="{poly}" fill="none" stroke="{CAT[0]}" stroke-width="2.5" '
            f'stroke-linejoin="round" stroke-linecap="round"/>{dots}</svg>')


def _svg_ci(pr: dict):
    """Barra de estimación con banda de intervalo (Wilson), en vista acercada."""
    wl = pr.get("wilson") or [0, 0]
    p = pr.get("p", 0)
    lo, hi = wl[0], wl[1]
    pad = max((hi - lo) * 1.5, 0.02)               # ventana con holgura alrededor del IC
    a, b = max(0.0, lo - pad), min(1.0, hi + pad)
    span = (b - a) or 1
    W = 520
    x = lambda f: 12 + (f - a) / span * (W - 24)   # noqa: E731
    return (f'<svg viewBox="0 0 {W} 66" width="100%" height="66" role="img" '
            f'aria-label="Estimación {fmt(p*100)}% con intervalo {fmt(lo*100)}–{fmt(hi*100)}%">'
            f'<line x1="12" y1="40" x2="{W-12}" y2="40" stroke="#e4e3dc"/>'
            f'<rect x="{x(lo):.1f}" y="30" width="{(x(hi)-x(lo)):.1f}" height="20" rx="10" '
            f'fill="rgba(42,120,214,.18)"/>'
            f'<line x1="{x(p):.1f}" y1="24" x2="{x(p):.1f}" y2="52" stroke="{CAT[0]}" stroke-width="3"/>'
            f'<text x="{x(p):.1f}" y="18" font-size="13" font-weight="700" fill="{CAT[0]}" '
            f'text-anchor="middle">{fmt(p*100)}%</text>'
            f'<text x="{x(lo):.1f}" y="64" font-size="10.5" fill="#898781" text-anchor="middle">{fmt(lo*100)}%</text>'
            f'<text x="{x(hi):.1f}" y="64" font-size="10.5" fill="#898781" text-anchor="middle">{fmt(hi*100)}%</text>'
            f'</svg>')


def _esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# --------------------------------------------------------------------------- #
#  Ensamblado del informe
# --------------------------------------------------------------------------- #

def build_report(panels: list[dict], *, titulo: str = "Informe de análisis",
                 subtitulo: str = "", fecha: str = "") -> str:
    """Construye el HTML del informe. Cada panel: {titulo, shape, rows, columns,
    value_col?, label_col?}."""
    secciones = []
    hallazgos_globales = []
    for p in panels:
        # Panel de proporción (encuesta / intención de voto): {k, n, population?}.
        if p.get("shape") == "proportion":
            pr = S.proportion_ci(p.get("k", 0), p.get("n", 0), population=p.get("population"))
            block = {"shape": "proportion", "proporcion": pr, "cautelas": []}
            if pr.get("n") and pr["n"] < 30:
                block["cautelas"].append(
                    f"Muestra pequeña (n={pr['n']}): el margen de error es amplio.")
            nar = narrate(block, p.get("titulo", ""))
            if nar["resumen"]:
                hallazgos_globales.append((p.get("titulo", ""), nar["resumen"][0]))
            secciones.append(_seccion(p.get("titulo", "Panel"), _svg_ci(pr), nar))
            continue

        rows = p.get("rows") or []
        cols = p.get("columns") or (list(rows[0].keys()) if rows else [])
        block = S.summarize_result(p.get("shape", ""), rows, cols,
                                   value_col=p.get("value_col"), label_col=p.get("label_col"))
        nar = narrate(block, p.get("titulo", ""))
        if nar["resumen"]:
            hallazgos_globales.append((p.get("titulo", ""), nar["resumen"][0]))
        # Gráfico
        lcol = p.get("label_col")
        vcol = p.get("value_col")
        if not (lcol and vcol) and rows:
            numc = [c for c in cols if all(S._f(r.get(c)) is not None for r in rows if r.get(c) is not None)]
            catc = [c for c in cols if c not in numc]
            vcol = vcol or (numc[-1] if numc else None)
            lcol = lcol or (catc[0] if catc else None)
        chart = ""
        if p.get("shape") == "timeseries" and vcol:
            chart = _svg_line(rows, lcol, vcol)
        elif p.get("shape") in ("category",) and lcol and vcol:
            chart = _svg_bars(rows, lcol, vcol)
        secciones.append(_seccion(p.get("titulo", "Panel"), chart, nar))

    resumen_ejecutivo = "".join(
        f"<li><b>{_esc(t)}:</b> {_esc(f)}</li>" for t, f in hallazgos_globales) \
        or "<li>Sin hallazgos.</li>"

    return _HTML.format(
        titulo=_esc(titulo), subtitulo=_esc(subtitulo or "Estadística real · resúmenes por gráfico"),
        fecha=_esc(fecha), resumen=resumen_ejecutivo, secciones="".join(secciones))


def _seccion(titulo, chart, nar) -> str:
    kpis = "".join(
        f'<div class="kpi"><div class="l">{_esc(k["label"])}</div>'
        f'<div class="v">{_esc(str(k["valor"]))}</div></div>' for k in nar["kpis"])
    resumen = "".join(f"<li>{_esc(f)}</li>" for f in nar["resumen"]) or "<li>—</li>"
    cautelas = ""
    if nar["cautelas"]:
        cautelas = ('<div class="caut"><b>Cautela.</b> '
                    + " ".join(_esc(c) for c in nar["cautelas"]) + "</div>")
    chart_html = f'<div class="chart">{chart}</div>' if chart else ""
    return (f'<section class="panel"><h3>{_esc(titulo)}</h3>'
            f'<div class="kpis">{kpis}</div>'
            f'{chart_html}'
            f'<ul class="res">{resumen}</ul>{cautelas}</section>')


_HTML = """<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📊</text></svg>"/>
<title>{titulo}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&family=Spline+Sans+Mono:wght@400;500&display=swap" rel="stylesheet"/>
<style>
 :root{{--brand:#1B3A6B;--brand-dark:#0F2444;--gold:#E8A838;--ink:#101418;--ink2:#52514e;--muted:#898781;--bg:#f4f5f2;--surface:#fff;--border:#e4e3dc}}
 *{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font-family:"Instrument Sans",system-ui,sans-serif;-webkit-font-smoothing:antialiased;line-height:1.55}}
 .wrap{{max-width:900px;margin:0 auto;padding:0 22px}}
 header{{background:linear-gradient(150deg,var(--brand-dark),var(--brand));color:#fff;padding:34px 0}}
 header h1{{margin:6px 0 4px;font-size:26px;letter-spacing:-.02em}}
 header p{{margin:0;color:#d6e2f5;font-size:14px}}
 .pill{{display:inline-block;font-size:11px;text-transform:uppercase;letter-spacing:.14em;color:var(--gold);font-weight:700}}
 main{{padding:26px 0 60px}}
 .exec{{background:var(--surface);border:1px solid var(--border);border-left:4px solid var(--gold);border-radius:12px;padding:16px 20px;margin-bottom:22px}}
 .exec h2{{margin:0 0 8px;font-size:15px;text-transform:uppercase;letter-spacing:.08em;color:var(--brand)}}
 .exec ul{{margin:0;padding-left:18px}} .exec li{{margin:4px 0;font-size:14px}}
 .panel{{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:20px;margin-bottom:16px;box-shadow:0 1px 2px rgba(15,36,68,.05)}}
 .panel h3{{margin:0 0 12px;font-size:17px}}
 .kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:14px}}
 @media(max-width:640px){{.kpis{{grid-template-columns:1fr 1fr}}}}
 .kpi{{background:#fbfbf9;border:1px solid var(--border);border-radius:10px;padding:10px}}
 .kpi .l{{font-size:10.5px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}}
 .kpi .v{{font-size:18px;font-weight:700;margin-top:2px}}
 .chart{{margin:6px 0 12px}}
 ul.res{{margin:6px 0 0;padding-left:18px}} ul.res li{{margin:5px 0;font-size:14px;color:var(--ink2)}}
 .caut{{margin-top:12px;background:#fff7e8;border:1px solid #f3dca0;border-radius:10px;padding:10px 12px;font-size:13px;color:#7a5b12}}
 footer{{color:var(--muted);font-size:12.5px;padding:0 0 40px}}
 code{{font-family:"Spline Sans Mono",monospace;font-size:12px}}
</style></head>
<body>
<header><div class="wrap"><span class="pill">Informe · Yachay Deep Analytics</span>
<h1>{titulo}</h1><p>{subtitulo}{fecha}</p></div></header>
<main class="wrap">
 <div class="exec"><h2>Resumen ejecutivo</h2><ul>{resumen}</ul></div>
 {secciones}
 <footer>Estadística real (numpy/scipy): descriptiva e inferencial. Los resúmenes se
 generan de forma determinista a partir de los cálculos — sin números inventados.
 Recuerda: correlación no implica causación; con muestras pequeñas, interpreta con cautela.</footer>
</main></body></html>"""
