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

from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from yd_analytics import build_model, ingest, make_router, registry

HERE = os.path.dirname(__file__)
DB = os.path.join(HERE, "studio.db")
_engine: Engine = create_engine(f"sqlite:///{DB}", connect_args={"check_same_thread": False})
_tables: list[str] = []


def get_engine() -> Engine:
    return _engine


app = FastAPI(title="yd-analytics · Studio")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(make_router(get_engine=get_engine))   # /analytics/query, /assist, /graph


def _slug(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", os.path.splitext(name)[0].lower()).strip("_")
    return s or "datos"


@app.get("/")
def index():
    return FileResponse(os.path.join(HERE, "studio.html"))


@app.post("/ingest")
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


@app.get("/health")
def health():
    return {"status": "ok", "tables": _tables}
