/* @yachaydeep/dashboard — Traductor ChartSpec + MetricResult → opciones de ECharts.

   El resolver del backend ya decidió QUÉ gráfico; aquí solo lo pintamos con los
   tokens de marca y el formateador es-EC. Ningún número se imprime sin pasar por
   format.ts (regla de casa).

   Regla de color: serie = --brand-primary; acento = --brand-accent (dorado).
   El VIOLETA está reservado a terceros: nunca aparece aquí.
*/
import type { ChartSpec, MetricResult, Formato } from "./types";
import { money, number as fmtNumber, percent } from "./format"; // formateador único de casa (es-EC)

const css = (v: string, fallback: string) =>
  (typeof getComputedStyle !== "undefined"
    ? getComputedStyle(document.documentElement).getPropertyValue(v).trim()
    : "") || fallback;

const PRIMARY = () => css("--brand-primary", "#1B3A6B");
const ACCENT = () => css("--brand-accent", "#E8A838");
const INK = () => css("--ink", "#11182a");
const MUTED = () => css("--muted", "#6B7280");

export function fmt(value: number, formato: Formato): string {
  if (formato === "money") return money(value);
  if (formato === "percent") return percent(value);
  return fmtNumber(value);
}

export function toEChartsOption(chart: ChartSpec, result: MetricResult) {
  const { rows, formato } = result;
  const axisFmt = (v: number) => fmt(v, formato);

  if (chart.type === "line" || chart.type === "area") {
    const x = chart.encoding.x.field;
    return {
      grid: { left: 48, right: 16, top: 24, bottom: 32 },
      tooltip: { trigger: "axis", valueFormatter: axisFmt },
      xAxis: { type: "category", data: rows.map((r) => r[x]), axisLine: { lineStyle: { color: MUTED() } } },
      yAxis: { type: "value", axisLabel: { formatter: axisFmt } },
      series: [{
        type: "line",
        smooth: true,
        areaStyle: chart.type === "area" ? { opacity: 0.15 } : undefined,
        data: rows.map((r) => r.valor),
        itemStyle: { color: PRIMARY() },
        lineStyle: { color: PRIMARY(), width: 2.5 },
      }],
    };
  }

  if (chart.type === "bar" || chart.type === "bar_h") {
    const cat = chart.encoding.x.field;
    const horizontal = chart.type === "bar_h";
    const catAxis = { type: "category", data: rows.map((r) => r[cat]) };
    const valAxis = { type: "value", axisLabel: { formatter: axisFmt } };
    return {
      grid: { left: horizontal ? 96 : 48, right: 16, top: 24, bottom: 32 },
      tooltip: { trigger: "item", valueFormatter: axisFmt },
      xAxis: horizontal ? valAxis : catAxis,
      yAxis: horizontal ? { ...catAxis, inverse: true } : valAxis,
      series: [{
        type: "bar",
        data: rows.map((r) => r.valor),
        itemStyle: { color: PRIMARY(), borderRadius: horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0] },
      }],
    };
  }

  if (chart.type === "heatmap") {
    const [xf, yf] = [chart.encoding.x.field, chart.encoding.y.field];
    const xs = [...new Set(rows.map((r) => r[xf] as string))];
    const ys = [...new Set(rows.map((r) => r[yf] as string))];
    const data = rows.map((r) => [xs.indexOf(r[xf] as string), ys.indexOf(r[yf] as string), r.valor]);
    const max = Math.max(...rows.map((r) => Number(r.valor)));
    return {
      grid: { left: 96, right: 16, top: 24, bottom: 48 },
      tooltip: { position: "top", valueFormatter: axisFmt },
      xAxis: { type: "category", data: xs },
      yAxis: { type: "category", data: ys },
      visualMap: { min: 0, max, calculable: true, orient: "horizontal", left: "center", bottom: 0,
        inRange: { color: ["#D8EFF4", PRIMARY()] } },  // hielo → primario (nunca violeta)
      series: [{ type: "heatmap", data, label: { show: true, formatter: (p: any) => axisFmt(p.value[2]) } }],
    };
  }

  // fallback: tabla
  return { _table: true, columns: result.columns, rows };
}
