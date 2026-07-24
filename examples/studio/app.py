"""
Studio — modo autoservicio: sube un Excel/CSV (o conecta una base) y obtén un tablero.

Ata todo el sistema: ingesta + limpieza (`ingest`) → perfilado (`profile`) → registro
de métricas → tablero propuesto → consultas (`/analytics/query`). Sirve también una UI
mínima (studio.html).

Uso:
    pip install -e ../../packages/py[api,ingest] python-multipart uvicorn
    uvicorn app:app --reload      # http://127.0.0.1:8000
"""
from __future__ import annotations

import os
import re
import tempfile

from fastapi import Body, Depends, FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from yd_analytics import (MetricQuery, build_model, ingest, make_auth, make_router,
                          openai_compatible_llm, registry, report, run_query, stats,
                          telemetry)
from yd_analytics.auth import allowed_origins

HERE = os.path.dirname(__file__)
DB = os.path.join(HERE, "studio.db")
# Producción: ANALYTICS_DB_URL apunta a la BD de la app (Postgres de Core, idealmente una
# VISTA de solo lectura sin PII — ver scripts/core_readonly_view.sql). Sin la variable,
# arranca con el SQLite de demo (studio.db).
_DB_URL = os.environ.get("ANALYTICS_DB_URL")
if _DB_URL:
    _engine: Engine = create_engine(_DB_URL, pool_pre_ping=True)
else:
    _engine: Engine = create_engine(f"sqlite:///{DB}", connect_args={"check_same_thread": False})
_tables: list[str] = []
_last_dashboard: list[dict] = []   # paneles del último tablero propuesto (para el informe)


def get_engine() -> Engine:
    return _engine


app = FastAPI(title="yd-analytics · Studio")

# --- Autenticación por API key + CORS restringido --------------------------- #
# En producción define YD_API_KEYS="clave:tenant:rol,..." (cierra el API) y
# YD_ALLOWED_ORIGINS="https://tu-app.com,..." (restringe el navegador). Sin
# llaves, arranca en modo ABIERTO (solo desarrollo) y avisa por log.
auth = make_auth()
_origins = allowed_origins(dev_open=not auth.require)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,          # con "*" no se permiten credenciales (regla CORS)
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- Asistente en lenguaje natural (Cerebras / OpenAI-compatible) ------------ #
# Se activa SOLO si hay clave en el entorno; si no, /assist usa reglas offline.
# En Railway define: LLM_API_KEY (o CEREBRAS_API_KEY), y opcionalmente LLM_BASE_URL
# (por defecto Cerebras) y LLM_MODEL.
_llm = None
_llm_key = os.environ.get("LLM_API_KEY") or os.environ.get("CEREBRAS_API_KEY")
if _llm_key:
    _llm = openai_compatible_llm(
        os.environ.get("LLM_BASE_URL", "https://api.cerebras.ai/v1"),
        _llm_key,
        os.environ.get("LLM_MODEL", "llama-3.3-70b"),
    )

# El router de datos (/analytics/query, /assist, /graph) usa la API key para
# resolver el ROL; los endpoints extra abajo exigen una llave válida.
app.include_router(make_router(get_engine=get_engine, get_role=auth.get_role, assist_llm=_llm))
_protected = [Depends(auth.get_principal)]

# --- Telemetría de producto (uso de Core/Áncora/Kullki y otras apps) --------- #
telemetry.ensure_events_table(_engine)
telemetry.register_telemetry()   # publica uso_usuarios_activos, uso_top_pantallas, ...

# Métricas por app (Opción A: un backend, tenant por llave). Cada app declara las suyas
# en yd_analytics/apps/. Core lee de las vistas analytics_ro (sin PII) vía ANALYTICS_DB_URL.
try:
    from yd_analytics.apps import core as _core_app
    _ids = _core_app.register_all()
    print(f"[analytics] métricas de Core registradas: {len(_ids)} ({', '.join(_ids)})")
except Exception as _e:  # no tumbar el arranque si una app falla
    print(f"[analytics] aviso: no se registraron las métricas de Core: {_e}")


@app.post("/telemetry/collect", dependencies=_protected)
async def telemetry_collect(payload: dict = Body(...)):
    """Recibe una tanda de eventos de uso desde una app de la casa.

    Cuerpo: {"tenant": "core", "events": [{producto, evento, pantalla, usuario_id,
    sesion_id, dispositivo, os, pais}, ...]}. `usuario_id` debe llegar seudonimizado.
    Luego el uso se consulta con las métricas `uso_*` vía /analytics/query."""
    events = payload.get("events") or []
    tenant = payload.get("tenant", "default")
    n = telemetry.record_events(get_engine(), events, tenant=tenant)
    return {"stored": n}


def _slug(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", os.path.splitext(name)[0].lower()).strip("_")
    return s or "datos"


@app.get("/")
def index():
    return FileResponse(os.path.join(HERE, "studio.html"))


@app.post("/ingest", dependencies=_protected)
async def ingest_file(file: UploadFile):
    """Sube un archivo → limpia, perfila, registra métricas y propone un tablero."""
    suffix = os.path.splitext(file.filename or "datos.csv")[1] or ".csv"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        path = tmp.name
    table = _slug(file.filename or "datos")
    rep = ingest(path, get_engine(), table)
    os.unlink(path)

    # registrar las métricas propuestas para que /analytics/query las sirva
    for m in rep.profile.metrics:
        registry.register(m)
    if table not in _tables:
        _tables.append(table)
    # recordar los paneles propuestos para el informe (/report)
    global _last_dashboard
    _last_dashboard = rep.profile.dashboard.get("paneles", [])

    # relaciones entre todas las tablas cargadas (si hay varias)
    rels = []
    if len(_tables) > 1:
        rels = [r.__dict__ for r in build_model(get_engine(), _tables).relationships]

    return {
        "table": table,
        "rows_in": rep.rows_in,
        "rows_out": rep.rows_out,
        "issues": rep.issues,
        "columns": rep.columns,
        "dashboard": rep.profile.dashboard,
        "relationships": rels,
    }


# --- Estadística real e informe --------------------------------------------- #

def _panel_data(metric: str, dimensions: list[str] | None):
    """Corre una métrica y devuelve (título, forma, filas, columnas)."""
    resp = run_query(get_engine(), MetricQuery(metric=metric, dimensions=dimensions or []))
    spec = registry.get(metric)
    r = resp.result
    return spec.titulo, r.shape, r.rows, r.columns


@app.post("/analytics/stats", dependencies=_protected)
def analytics_stats(payload: dict = Body(...)):
    """Estadística real (descriptiva + inferencial) de una métrica."""
    metric = payload.get("metric")
    dims = payload.get("dimensions") or []
    titulo, shape, rows, cols = _panel_data(metric, dims)
    return {"metric": metric, "titulo": titulo,
            "stats": stats.summarize_result(shape, rows, cols)}


@app.post("/report", dependencies=_protected)
def build_report_endpoint(payload: dict = Body(default={})):
    """Genera un INFORME en HTML con resúmenes de cada gráfico.

    Cuerpo opcional: {"titulo": "...", "panels": [{"metric": "...", "dimensions": [...],
    "titulo": "..."}]}. Si no se pasan paneles, usa el último tablero propuesto."""
    panels_in = payload.get("panels") or _last_dashboard
    paneles = []
    for p in panels_in:
        # Paneles directos (ya traen sus datos): proporción {k,n} o filas propias.
        if p.get("shape") == "proportion" or p.get("rows") is not None:
            paneles.append(p)
            continue
        # Paneles por métrica: se resuelven con el motor.
        metric = p.get("metric")
        if not metric:
            continue
        try:
            titulo, shape, rows, cols = _panel_data(metric, p.get("dimensions"))
        except Exception:
            continue
        paneles.append({"titulo": p.get("titulo") or titulo, "shape": shape,
                        "rows": rows, "columns": cols})
    html = report.build_report(
        paneles, titulo=payload.get("titulo", "Informe de análisis"),
        subtitulo="Estadística real · resúmenes por gráfico")
    return HTMLResponse(content=html)


@app.get("/health")
def health():
    return {"status": "ok", "tables": _tables,
            "asistente": "llm" if _llm else "reglas"}
