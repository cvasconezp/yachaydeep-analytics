/* @yachaydeep/dashboard — ChoroplethView: mapa coroplético (forma "geo").

   Registra un GeoJSON en ECharts y pinta una región por magnitud con la rampa
   secuencial de la casa. El GeoJSON se pasa como prop (el paquete no fija ningún
   país): para Ecuador, usa packages/dashboard/geo/ecuador.json (provincias).

   Requiere: npm i echarts react
*/
import { useEffect, useRef } from "react";
import * as echarts from "echarts";
import { SEQUENTIAL } from "./palette";

export interface ChoroplethProps {
  /** GeoJSON FeatureCollection; las features llevan properties.name. */
  geojson: any;
  /** Nombre con que se registra el mapa (único por app). */
  mapName?: string;
  /** Datos por región: { name: <properties.name>, value: number }. */
  data: { name: string; value: number }[];
  height?: number;
  onSelect?: (name: string | null) => void;
}

export function ChoroplethView({ geojson, mapName = "ecuador", data, height = 460, onSelect }: ChoroplethProps) {
  const ref = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    echarts.registerMap(mapName, geojson);
    const chart = chartRef.current ?? echarts.init(ref.current);
    chartRef.current = chart;
    const max = Math.max(1, ...data.map((d) => d.value));
    chart.setOption({
      tooltip: { trigger: "item", formatter: (p: any) => `${p.name}: ${p.value ?? "—"}` },
      visualMap: {
        min: 0, max, left: 8, bottom: 8, calculable: true,
        inRange: { color: [SEQUENTIAL[0], SEQUENTIAL[3], SEQUENTIAL[6]] },
      },
      series: [{
        type: "map", map: mapName, roam: true, data,
        emphasis: { label: { show: true }, itemStyle: { areaColor: "#E8A838" } }, // acento dorado al hover
        itemStyle: { borderColor: "#fff", borderWidth: 0.5 },
        label: { show: false },
      }],
    }, true);
    const onClick = (p: any) => onSelect?.(p?.name ?? null);
    chart.off("click"); chart.on("click", onClick);
    const onResize = () => chart.resize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [geojson, mapName, data, onSelect]);

  useEffect(() => () => { chartRef.current?.dispose(); chartRef.current = null; }, []);

  return <div ref={ref} style={{ width: "100%", height }} />;
}
