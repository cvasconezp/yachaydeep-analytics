/* @yachaydeep/dashboard — La "cara" del sistema de analítica de la casa.
   Componentes React que consumen el contrato y pintan con ECharts. */
export { Dashboard } from "./Dashboard";
export { Panel } from "./Panel";
export { NetworkView } from "./NetworkView";
export type { NetworkViewProps } from "./NetworkView";
export { useMetric } from "./useMetric";
export { useFilters } from "./filterStore";
export { toEChartsOption, fmt } from "./chartOptions";
export * as format from "./format";
export type * from "./types";
