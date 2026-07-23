"""
yd_analytics — El cerebro del sistema de representación gráfica de la casa.

Paquete instalable que Core, Áncora y Kullki consumen por versión. Lee datos,
los interpreta (motor + resolver) y expone un contrato HTTP; el frontend
(@yachaydeep/dashboard) los pinta.

Uso mínimo:
    from yd_analytics import run_query, MetricQuery, make_router
    resp = run_query(engine, MetricQuery(metric="...", dimensions=["carrera"]), role="coordinador")
    # resp.result -> datos normalizados ; resp.chart -> cómo pintarlo

Grafos:            from yd_analytics import run_graph
Perfilado auto:    from yd_analytics import profile
Router para la app: from yd_analytics import make_router
"""
from __future__ import annotations

from sqlalchemy.engine import Engine

from . import graph, registry, resolver
from .assist import Suggestion, interpret, openai_compatible_llm
from .engine import run
from .export import to_csv
from .graph import run_graph
from .profiler import ProfiledColumn, ProfileResult, profile
from .schemas import (
    ChartSpec, Filter, GraphEdge, GraphNode, GraphResult, GraphSpec,
    MetricQuery, MetricResult, MetricSpec, PanelResponse,
)

__version__ = "0.1.0"

__all__ = [
    "run_query", "run_graph", "profile", "interpret", "openai_compatible_llm",
    "to_csv", "make_router",
    "registry", "resolver", "graph",
    "MetricQuery", "MetricResult", "MetricSpec", "ChartSpec", "Filter",
    "GraphSpec", "GraphNode", "GraphEdge", "GraphResult", "PanelResponse",
    "ProfileResult", "ProfiledColumn", "Suggestion", "__version__",
]


def run_query(engine: Engine, query: MetricQuery, *, role: str = "*",
              decrypt_labels=None) -> PanelResponse:
    """Punto de entrada tabular: ejecuta la métrica y resuelve su gráfico.

    decrypt_labels(dim, hashes)->{hash: texto}: hook opcional que la app provee
    para traducir etiquetas de índice ciego. El paquete NUNCA tiene las llaves;
    solo la app (con yd/crypto) descifra el puñado de etiquetas visibles."""
    spec = registry.get(query.metric)
    result = run(engine, query, role=role, decrypt_labels=decrypt_labels)
    chart = resolver.resolve(spec, query, result)
    return PanelResponse(result=result, chart=chart)


def make_router(**kwargs):
    """Factoría del APIRouter (import diferido para evitar dependencia de FastAPI
    si solo se usa el motor). Ver yd_analytics.router.make_router."""
    from .router import make_router as _mk
    return _mk(**kwargs)
