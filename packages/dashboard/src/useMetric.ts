/* @yachaydeep/dashboard — Hook de consulta de una métrica.

   Llama al contrato POST /analytics/query con los filtros globales activos.
   Usa TanStack Query para caché, reintentos y estados de carga.
   Requiere: npm i @tanstack/react-query
*/
import { useQuery } from "@tanstack/react-query";
import { useFilters } from "./filterStore";
import type { PanelResponse, PanelSpec } from "./types";

const API = import.meta.env.VITE_ANALYTICS_API ?? "http://127.0.0.1:8000";

async function fetchPanel(spec: PanelSpec, filters: unknown[]): Promise<PanelResponse> {
  const res = await fetch(`${API}/analytics/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include", // cookie de sesión (yd.auth) → el backend deduce el rol
    body: JSON.stringify({
      metric: spec.metric,
      dimensions: spec.dimensions ?? [],
      grain: spec.grain ?? null,
      chart_hint: spec.chartHint ?? null,
      filters,
      // params (p. ej. umbral) pueden venir de un contexto de tablero; omitido aquí
    }),
  });
  if (!res.ok) throw new Error(`analytics ${res.status}: ${await res.text()}`);
  return res.json();
}

export function useMetric(spec: PanelSpec) {
  const filters = useFilters((s) => s.filters);
  const arr = Object.values(filters);
  return useQuery({
    queryKey: ["panel", spec.id, spec.metric, spec.dimensions, arr],
    queryFn: () => fetchPanel(spec, arr),
    staleTime: 30_000,
  });
}
