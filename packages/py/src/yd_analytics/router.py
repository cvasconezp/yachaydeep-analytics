"""
yd_analytics.router — Factoría del APIRouter que cada app monta bajo /analytics.

El paquete NO conoce la app: recibe un proveedor de Engine y (opcional) una
dependencia de rol. Así Core, Áncora y Kullki lo montan con SU BD y SU auth.

    from fastapi import FastAPI
    from yd_analytics import make_router
    app = FastAPI()
    app.include_router(make_router(get_engine=lambda: engine))
    # rol real:  make_router(get_engine=..., get_role=deps_de_yd_auth)
"""
from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from .schemas import Filter, GraphResult, MetricQuery, PanelResponse


class GraphQuery(BaseModel):
    filters: list[Filter] = []


class AssistBody(BaseModel):
    question: str


def make_router(*, get_engine: Callable[[], object],
                get_role: Callable[..., str] | None = None,
                assist_llm: Callable[[str], dict] | None = None,
                prefix: str = "/analytics") -> APIRouter:
    # Imports internos diferidos para evitar ciclos con el __init__ del paquete.
    from . import registry, run_query
    from . import graph as graph_mod
    from .assist import interpret

    router = APIRouter(prefix=prefix, tags=["analytics"])

    if get_role is None:
        def get_role(x_demo_role: str = Header(default="admin")) -> str:  # noqa: PLW0642
            return x_demo_role

    @router.get("/registry")
    def list_metrics(role: str = Depends(get_role)):
        return [
            {"id": s.id, "titulo": s.titulo, "clase": s.clase, "shape": s.shape,
             "grano": s.grano, "version": s.version}
            for s in registry.visible_for(role)
        ]

    @router.post("/query", response_model=PanelResponse)
    def query(q: MetricQuery, role: str = Depends(get_role)):
        try:
            return run_query(get_engine(), q, role=role)
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/assist")
    def assist(body: AssistBody, role: str = Depends(get_role)):
        """Pregunta en lenguaje natural → sugerencia + panel resuelto.
        Con assist_llm (p.ej. Cerebras) usa el modelo; si no, reglas offline."""
        try:
            specs = registry.visible_for(role)
            sug = interpret(body.question, specs, llm=assist_llm)
            panel = run_query(get_engine(), sug.query, role=role)
            return {
                "suggestion": {"metric": sug.query.metric, "dimensions": sug.query.dimensions,
                               "chart_hint": sug.chart_hint, "rationale": sug.rationale,
                               "confidence": sug.confidence},
                "result": panel.result, "chart": panel.chart,
            }
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/graph/{graph_id}", response_model=GraphResult)
    def graph(graph_id: str, body: GraphQuery | None = None, role: str = Depends(get_role)):
        try:
            filters = body.filters if body else []
            return graph_mod.run_graph(get_engine(), graph_id, filters=filters, role=role)
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    return router
