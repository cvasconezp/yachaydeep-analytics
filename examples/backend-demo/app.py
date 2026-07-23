"""
Ejemplo de app que consume yd-analytics como paquete.

Muestra lo esencial: importar make_router y montarlo con SU proveedor de Engine.
En producción, get_role saldría de yd.auth (baseline de la casa) en vez del header.

Uso:
    pip install -e ../../packages/py ".[api]"   # o: pip install yd-analytics[api]
    python seed_demo.py && python seed_graph.py
    uvicorn app:app --reload                     # http://127.0.0.1:8000/docs
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from yd_analytics import make_router
from db import get_engine

app = FastAPI(title="ejemplo · yd-analytics")

# Demo local: CORS abierto solo para desarrollo (el ejemplo Vite lo consume).
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# El paquete no conoce la app: recibe el proveedor de Engine.
app.include_router(make_router(get_engine=get_engine))


@app.get("/health")
def health():
    return {"status": "ok"}
