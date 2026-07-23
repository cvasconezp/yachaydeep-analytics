/* @yachaydeep/dashboard — NetworkView: la forma "graph" con estilo VOSviewer.

   Render de redes: aristas curvas translúcidas coloreadas por el clúster de origen
   (sin flechas), nodos con sombreado de esfera y tamaño por peso, etiquetas al lado.
   Dos modos de color: "cluster" (comunidad, discreto) u "overlay" (atributo numérico
   continuo, escala viridis con leyenda) — los dos modos característicos de VOSviewer.

   Requiere: npm i echarts react
*/
import { useEffect, useRef } from "react";
import * as echarts from "echarts";
import type { GraphResult, GraphNode } from "./types";

const VIRIDIS = ["#440154", "#46327e", "#365c8d", "#277f8e", "#1fa187", "#4ac16d", "#a0da39", "#fde725"];
const hex2rgb = (h: string) => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
const lerp = (a: number, b: number, t: number) => Math.round(a + (b - a) * t);
function viridis(t: number): string {
  t = Math.max(0, Math.min(1, t));
  const s = t * (VIRIDIS.length - 1), i = Math.floor(s), f = s - i;
  if (i >= VIRIDIS.length - 1) return VIRIDIS[VIRIDIS.length - 1];
  const a = hex2rgb(VIRIDIS[i]), b = hex2rgb(VIRIDIS[i + 1]);
  return `rgb(${lerp(a[0], b[0], f)},${lerp(a[1], b[1], f)},${lerp(a[2], b[2], f)})`;
}
function lighten(hex: string, amt: number): string {
  const [r, g, b] = hex2rgb(hex); const f = (x: number) => Math.round(x + (255 - x) * amt);
  return `rgb(${f(r)},${f(g)},${f(b)})`;
}
function sphere(color: string) {
  return new echarts.graphic.RadialGradient(0.32, 0.3, 0.85, [
    { offset: 0, color: color.startsWith("#") ? lighten(color, 0.35) : color },
    { offset: 1, color },
  ]);
}

export interface NetworkViewProps {
  data: GraphResult;
  colorBy?: "cluster" | "overlay";
  /** clúster (comunidad) de un nodo → nombre + color. Por defecto usa node.group. */
  clusterOf?: (n: GraphNode) => { name: string; color: string };
  /** valor numérico para el overlay continuo. Por defecto usa node.value. */
  overlayValue?: (n: GraphNode) => number;
  height?: number;
  onSelect?: (id: string | null) => void;
}

const CLUSTER_PALETTE = ["#E4A11B", "#2B6FD6", "#17A398", "#E4572E", "#6B7A8F", "#4CA64C"]; // sin violeta

export function NetworkView({
  data, colorBy = "cluster", clusterOf, overlayValue, height = 600, onSelect,
}: NetworkViewProps) {
  const ref = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    const chart = chartRef.current ?? echarts.init(ref.current);
    chartRef.current = chart;

    const groups = Array.from(new Set(data.nodes.map((n) => n.group ?? "—")));
    const defClusterColor = (n: GraphNode) =>
      CLUSTER_PALETTE[groups.indexOf(n.group ?? "—") % CLUSTER_PALETTE.length];
    const clusterFor = (n: GraphNode) => clusterOf ? clusterOf(n) : { name: String(n.group ?? "—"), color: defClusterColor(n) };
    const ovVal = (n: GraphNode) => (overlayValue ? overlayValue(n) : (n.value ?? 1));
    const vals = data.nodes.map(ovVal);
    const vmin = Math.min(...vals), vmax = Math.max(...vals);

    const solidOf = (n: GraphNode) =>
      colorBy === "overlay" ? viridis((ovVal(n) - vmin) / (vmax - vmin || 1)) : clusterFor(n).color;

    const nodes = data.nodes.map((n) => {
      const solid = solidOf(n);
      return {
        id: n.id, name: n.id, value: ovVal(n),
        symbolSize: 12 + (n.value ?? 1) * 5,
        itemStyle: { color: colorBy === "overlay" ? solid : sphere(solid), borderWidth: 0, shadowBlur: 8, shadowColor: "rgba(30,40,60,.18)" },
        label: { show: true, position: "right", distance: 4, color: "#2a2f3a", fontSize: 10,
          formatter: n.label.length > 18 ? n.id : n.label },
        _solid: solid,
      };
    });
    const cmap: Record<string, string> = {}; nodes.forEach((d: any) => (cmap[d.id] = d._solid));
    const links = data.edges.map((e) => {
      const c = cmap[e.source] ?? "#94a3b8";
      const rgb = /^rgb/.test(c) ? c.match(/\d+/g)!.map(Number) : hex2rgb(c);
      return { source: e.source, target: e.target,
        lineStyle: { color: `rgba(${rgb[0]},${rgb[1]},${rgb[2]},0.42)`, width: 1.1, curveness: 0.28 } };
    });

    chart.setOption({
      tooltip: { formatter: (p: any) => p.dataType === "node"
        ? `<b>${data.nodes.find((n) => n.id === p.name)?.label ?? p.name}</b>` : "" },
      visualMap: colorBy === "overlay" ? {
        type: "continuous", min: vmin, max: vmax, calculable: true, orient: "horizontal",
        right: 20, bottom: 10, inRange: { color: VIRIDIS }, dimension: 0, seriesIndex: 0,
      } : undefined,
      series: [{
        type: "graph", layout: "force", roam: true, draggable: true,
        force: { repulsion: 900, edgeLength: [90, 210], gravity: 0.035, friction: 0.12 },
        edgeSymbol: ["none", "none"],
        emphasis: { focus: "adjacency", label: { fontWeight: "bold" }, lineStyle: { width: 2.4, opacity: 0.8 } },
        data: nodes, links,
      }],
    }, true);

    const onClick = (p: any) => { if (p?.dataType === "node") onSelect?.(p.name); };
    chart.off("click"); chart.on("click", onClick);
    const onResize = () => chart.resize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [data, colorBy, clusterOf, overlayValue, onSelect]);

  useEffect(() => () => { chartRef.current?.dispose(); chartRef.current = null; }, []);

  return <div ref={ref} style={{ width: "100%", height }} />;
}
