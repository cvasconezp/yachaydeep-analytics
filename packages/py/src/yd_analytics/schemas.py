"""
yd.analytics.schemas — Contratos tipados del módulo de tableros de la casa.

Estos objetos son la frontera entre capas y la unidad de versionado
(ver docs/DASHBOARD.md §3). Pydantic v2.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# --- Vocabulario cerrado --------------------------------------------------- #

Clase = Literal["uso", "dominio", "impacto"]
Shape = Literal[
    "scalar",
    "timeseries",
    "category",
    "category_wide",
    "part_to_whole",
    "timeseries_multi",
    "distribution",
    "correlation",
    "matrix",
    "funnel",
    "table",
]
Formato = Literal["number", "money", "percent", "impact"]
ChartType = Literal[
    "kpi", "line", "area", "bar", "bar_h", "stacked_bar", "treemap",
    "scatter", "heatmap", "funnel", "table", "pie", "histogram", "boxplot",
]
FilterOp = Literal["eq", "in", "gte", "lte", "between"]


# --- Métrica declarada (evolución máquina-legible del DATA_DICTIONARY) ------ #

class Measure(BaseModel):
    """Expresión SQL de agregación. Es la ÚNICA parte con SQL libre; se define
    en el registro de casa, nunca llega desde el cliente."""
    sql: str


class MetricSpec(BaseModel):
    id: str
    clase: Clase
    titulo: str
    descripcion: str = ""
    shape: Shape                         # forma por defecto (0 dimensiones)
    unidad: str = "conteo"
    formato: Formato = "number"
    fuente: str                          # vista/tabla (whitelist de FROM)
    medida: Measure
    grano: list[str] = Field(default_factory=list)   # dimensiones permitidas
    dim_temporal: str | None = None
    cadencia: Literal["on-read", "hourly", "daily"] = "on-read"
    modelo: dict[str, str] | None = None
    # Valores por defecto de los parámetros de la medida (p. ej. {"umbral": 0.7}),
    # usados cuando la consulta no los provee (asistencia, tableros automáticos).
    param_defaults: dict[str, Any] = Field(default_factory=dict)
    roles: list[str] = Field(default_factory=lambda: ["*"])
    # --- Privacidad / cifrado (ver docs de seguridad) --- #
    # Para una dimensión cifrada, la columna del índice ciego (blind index) que
    # permite agrupar/igualar sin exponer el texto plano. { "cedula": "cedula_bidx" }.
    blind_index: dict[str, str] = Field(default_factory=dict)
    # Supresión k-anónima: si > 0 y la métrica es de conteo, se ocultan las celdas
    # con conteo < k (LOPDP: evita re-identificar grupos diminutos).
    k_anon: int = 0
    version: str = "v1"


# --- Consulta de un panel (request) ---------------------------------------- #

class Filter(BaseModel):
    field: str
    op: FilterOp = "eq"
    value: Any


class MetricQuery(BaseModel):
    metric: str
    dimensions: list[str] = Field(default_factory=list)
    grain: str | None = None
    filters: list[Filter] = Field(default_factory=list)
    params: dict[str, Any] = Field(default_factory=dict)
    limit: int | None = None
    chart_hint: ChartType | None = None


# --- Resultado del motor (response) ---------------------------------------- #

class Truncation(BaseModel):
    shown: int
    total: int
    grouped_as: str = "Otros"


class MetricResult(BaseModel):
    metric: str
    shape: Shape                         # forma EFECTIVA (según dimensiones)
    unidad: str
    formato: Formato
    columns: list[str]
    rows: list[dict[str, Any]]
    meta: dict[str, Any] = Field(default_factory=dict)
    truncated: Truncation | None = None


# --- Especificación de gráfico (la produce el resolver) -------------------- #

class Encoding(BaseModel):
    field: str
    type: Literal["nominal", "ordinal", "quantitative", "temporal"]
    format: Formato | None = None


class Interactions(BaseModel):
    emits_filter: str | None = None      # campo que filtra al hacer clic
    drilldown: list[str] = Field(default_factory=list)
    tooltip: list[str] = Field(default_factory=list)


class ChartSpec(BaseModel):
    type: ChartType
    encoding: dict[str, Encoding] = Field(default_factory=dict)
    interactions: Interactions = Field(default_factory=Interactions)
    series_role: Literal["primary", "accent", "neutral"] = "primary"
    note: str | None = None              # honestidad: recortes, etc.


class PanelResponse(BaseModel):
    result: MetricResult
    chart: ChartSpec


# --- Forma de RELACIONES: grafo de nodos (shape "graph") ------------------- #
# No es tidy (métrica × dimensiones): es una red. Contrato propio nodes+edges.

class GraphNode(BaseModel):
    id: str
    label: str
    group: str | None = None           # categoría (p. ej. nivel/área) → color
    value: float = 1.0                 # peso → tamaño (p. ej. criticidad)
    attrs: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    target: str
    weight: float = 1.0
    kind: str | None = None            # tipo de vínculo (p. ej. "prerrequisito")


class GraphResult(BaseModel):
    graph: str
    directed: bool = True
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    meta: dict[str, Any] = Field(default_factory=dict)


class GraphSpec(BaseModel):
    """Métrica de relación: dos consultas whitelisted (nodos y aristas)."""
    id: str
    clase: Clase = "dominio"
    titulo: str
    descripcion: str = ""
    directed: bool = True
    nodes_from: str                    # tabla/vista de nodos (whitelist FROM)
    node_id: str                       # columna id
    node_label: str                    # columna etiqueta
    node_group: str | None = None      # columna de categoría (color)
    edges_from: str                    # tabla/vista de aristas
    edge_source: str                   # columna origen
    edge_target: str                   # columna destino
    filterable: list[str] = Field(default_factory=list)  # campos filtrables (nodos)
    roles: list[str] = Field(default_factory=lambda: ["*"])
    version: str = "v1"
