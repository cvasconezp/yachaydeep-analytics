/* @yachaydeep-yd/analytics-contract
   Fuente de verdad de los tipos del sistema de analítica de la casa.
   Espejo de yd_analytics.schemas (Python). Los JSON Schema en ./schema se generan
   desde los modelos Pydantic (scripts/gen_schema.py) para validación cross-lenguaje. */

export type Clase = "uso" | "dominio" | "impacto";
export type Formato = "number" | "money" | "percent" | "impact";
export type Shape =
  | "scalar" | "timeseries" | "category" | "category_wide" | "part_to_whole"
  | "timeseries_multi" | "distribution" | "correlation" | "matrix" | "funnel" | "table";
export type ChartType =
  | "kpi" | "line" | "area" | "bar" | "bar_h" | "stacked_bar" | "treemap"
  | "scatter" | "heatmap" | "funnel" | "table" | "graph"
  | "pie" | "histogram" | "boxplot";
export type FilterOp = "eq" | "in" | "gte" | "lte" | "between";

export interface Measure { sql: string; }

export interface MetricSpec {
  id: string;
  clase: Clase;
  titulo: string;
  descripcion?: string;
  shape: Shape;
  unidad?: string;
  formato?: Formato;
  fuente: string;
  medida: Measure;
  grano?: string[];
  dim_temporal?: string | null;
  cadencia?: "on-read" | "hourly" | "daily";
  modelo?: Record<string, string> | null;
  roles?: string[];
  /** Para una dimensión cifrada: su columna de índice ciego (blind index). */
  blind_index?: Record<string, string>;
  /** Supresión k-anónima: oculta conteos < k (LOPDP). 0 = desactivado. */
  k_anon?: number;
  version?: string;
}

export interface Filter { field: string; op?: FilterOp; value: unknown; }

export interface MetricQuery {
  metric: string;
  dimensions?: string[];
  grain?: string | null;
  filters?: Filter[];
  params?: Record<string, unknown>;
  limit?: number | null;
  chart_hint?: ChartType | null;
}

export interface Truncation { shown: number; total: number; grouped_as: string; }

export interface MetricResult {
  metric: string;
  shape: Shape;
  unidad: string;
  formato: Formato;
  columns: string[];
  rows: Record<string, unknown>[];
  meta: Record<string, unknown>;
  truncated?: Truncation | null;
}

export interface Encoding { field: string; type: "nominal" | "ordinal" | "quantitative" | "temporal"; format?: Formato; }
export interface Interactions { emits_filter?: string | null; drilldown: string[]; tooltip: string[]; }
export interface ChartSpec {
  type: ChartType;
  encoding: Record<string, Encoding>;
  interactions: Interactions;
  series_role: "primary" | "accent" | "neutral";
  note?: string | null;
}
export interface PanelResponse { result: MetricResult; chart: ChartSpec; }

/* ---- Grafos (shape "graph") ---- */
export interface GraphNode { id: string; label: string; group?: string | null; value?: number; attrs?: Record<string, unknown>; }
export interface GraphEdge { source: string; target: string; weight?: number; kind?: string | null; }
export interface GraphResult { graph: string; directed: boolean; nodes: GraphNode[]; edges: GraphEdge[]; meta?: Record<string, unknown>; }

/* ---- Tablero declarativo ---- */
export interface PanelSpec {
  id: string; metric: string; dimensions?: string[]; grain?: string | null;
  chartHint?: ChartType | null; size?: "sm" | "md" | "lg";
}
export interface DashboardSpec {
  id: string; titulo: string; filtrosGlobales: string[]; paneles: PanelSpec[];
}
