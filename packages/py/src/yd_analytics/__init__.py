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
from .model import Model, Relationship, build_model, detect_relationships, query_related
from .profiler import ProfiledColumn, ProfileResult, profile
from .tenancy import Tenant, TenantResolver, make_get_engine, row_filter, tenant_from_host
from .schemas import (
    ChartSpec, Filter, GraphEdge, GraphNode, GraphResult, GraphSpec,
    MetricQuery, MetricResult, MetricSpec, PanelResponse,
)

__version__ = "0.2.0"

__all__ = [
    "run_query", "run_graph", "profile", "interpret", "openai_compatible_llm",
    "ingest", "to_csv", "make_router", "make_auth", "ApiKey",
    "detect_relationships", "build_model", "query_related", "Model", "Relationship",
    "TenantResolver", "Tenant", "make_get_engine", "tenant_from_host", "row_filter",
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


def make_auth(**kwargs):
    """Factoría de dependencias de autenticación por API key (import diferido:
    requiere el extra `[api]` con FastAPI). Ver yd_analytics.auth.make_auth."""
    from .auth import make_auth as _ma
    return _ma(**kwargs)


from .auth import ApiKey  # noqa: E402  (dataclass puro, sin FastAPI)


def ingest(*args, **kwargs):
    """Ingesta y limpieza de Excel/CSV → tabla + perfil (import diferido: requiere
    el extra `[ingest]` con pandas/openpyxl). Ver yd_analytics.ingest.ingest."""
    from .ingest import ingest as _ing
    return _ing(*args, **kwargs)
