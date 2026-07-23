/* @yachaydeep/dashboard — Exportación de un panel: CSV y PNG.
   Exporta los AGREGADOS mostrados (nunca filas crudas de PII). */
import type { MetricResult } from "./types";

export function toCSV(result: MetricResult): string {
  const cols = result.columns;
  const head = cols.join(",");
  const body = result.rows.map((r) =>
    cols.map((c) => {
      const v = r[c as keyof typeof r];
      const s = v == null ? "" : String(v);
      return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
    }).join(",")
  );
  return [head, ...body].join("\n");
}

function download(name: string, mime: string, data: string | Blob) {
  const url = URL.createObjectURL(typeof data === "string" ? new Blob([data], { type: mime }) : data);
  const a = document.createElement("a");
  a.href = url; a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function exportCSV(result: MetricResult, filename = "datos.csv") {
  download(filename, "text/csv;charset=utf-8", "﻿" + toCSV(result)); // BOM → Excel es-EC
}

/** PNG desde una instancia de ECharts (chart.getDataURL). */
export function exportPNG(chart: { getDataURL: (o?: any) => string }, filename = "grafico.png") {
  const url = chart.getDataURL({ pixelRatio: 2, backgroundColor: "#fff" });
  const a = document.createElement("a"); a.href = url; a.download = filename; a.click();
}
