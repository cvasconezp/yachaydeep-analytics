/* @yachaydeep/dashboard — Tipos.
   Los tipos del contrato viven en @yachaydeep/analytics-contract (fuente de verdad).
   Este módulo los re-exporta para que los componentes importen desde "./types". */
export type {
  Clase, Formato, Shape, ChartType, FilterOp, Measure, MetricSpec, Filter,
  MetricQuery, Truncation, MetricResult, Encoding, Interactions, ChartSpec,
  PanelResponse, GraphNode, GraphEdge, GraphResult, PanelSpec, DashboardSpec,
} from "@yachaydeep/analytics-contract";
