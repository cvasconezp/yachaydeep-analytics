/* @yachaydeep-yd/dashboard — La "cara" del sistema de analítica de la casa.
   Componentes React que consumen el contrato y pintan con ECharts. */
export { Dashboard } from "./Dashboard";
export type { DashboardProps } from "./Dashboard";
export { AttributionBadge, ANALYTICS_COLOR } from "./AttributionBadge";
export type { AttributionBadgeProps } from "./AttributionBadge";
export { Panel } from "./Panel";
export { NetworkView } from "./NetworkView";
export type { NetworkViewProps } from "./NetworkView";
export { ChoroplethView } from "./ChoroplethView";
export type { ChoroplethProps } from "./ChoroplethView";
export { useMetric } from "./useMetric";
export { configureAnalytics, analyticsBase, analyticsHeaders, analyticsCredentials } from "./client";
export type { AnalyticsClientConfig } from "./client";
export { useFilters } from "./filterStore";
export { toEChartsOption, fmt } from "./chartOptions";
export { toCSV, exportCSV, exportPNG } from "./export";
export * as palette from "./palette";
export * as format from "./format";
export type * from "./types";
