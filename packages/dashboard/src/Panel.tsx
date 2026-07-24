/* @yachaydeep-yd/dashboard — Un panel: consulta una métrica y la pinta.
   Requiere: npm i echarts echarts-for-react
*/
import { useMemo } from "react";
import ReactECharts from "echarts-for-react";
import { useMetric } from "./useMetric";
import { useFilters } from "./filterStore";
import { toEChartsOption, fmt } from "./chartOptions";
import type { PanelSpec } from "./types";

export function Panel({ spec }: { spec: PanelSpec }) {
  const { data, isLoading, error } = useMetric(spec);
  const toggle = useFilters((s) => s.toggle);

  const option = useMemo(
    () => (data ? toEChartsOption(data.chart, data.result) : null),
    [data]
  );

  if (isLoading) return <div className="yd-panel yd-panel--loading">Cargando…</div>;
  if (error) return <div className="yd-panel yd-panel--error">Error: {String(error)}</div>;
  if (!data) return null;

  const { chart, result } = data;

  // KPI: número grande + clase de métrica (uso/dominio/impacto).
  if (chart.type === "kpi") {
    const valor = Number(result.rows[0]?.valor ?? 0);
    return (
      <div className="yd-panel yd-kpi">
        <div className="yd-kpi__value">{fmt(valor, result.formato)}</div>
        <div className="yd-kpi__label">{spec.titulo ?? spec.metric}</div>
      </div>
    );
  }

  // Interacción: clic en una marca emite un filtro (cross-filtering).
  const onEvents: Record<string, (p: any) => void> = chart.interactions.emits_filter
    ? {
        click: (p: any) => {
          const field = chart.interactions.emits_filter!;
          const value = p.name; // categoría clicada
          toggle(field, value);
        },
      }
    : {};

  return (
    <div className="yd-panel">
      <div className="yd-panel__head">
        <h3>{spec.titulo ?? spec.metric}</h3>
        {(spec.nota || chart.note) && <p className="yd-panel__note">{spec.nota ?? chart.note}</p>}
      </div>
      <ReactECharts option={option} onEvents={onEvents} style={{ height: 280 }} notMerge />
    </div>
  );
}
