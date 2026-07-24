/* @yachaydeep-yd/dashboard — Estado de filtros compartido (cross-filtering).

   Zustand + sincronización con la URL (tablero compartible, respeta atrás/adelante).
   Todos los paneles leen de aquí; al hacer clic en una marca, el panel emite un
   filtro y TODOS re-consultan. Esta es la pieza que hace "vivo" al tablero.

   Requiere: npm i zustand
*/
import { create } from "zustand";
import type { Filter } from "./types";

interface FilterState {
  filters: Record<string, Filter>;         // por campo (un filtro activo por campo)
  set: (field: string, value: unknown, op?: Filter["op"]) => void;
  toggle: (field: string, value: unknown) => void;   // clic en una marca ya activa la quita
  clear: (field?: string) => void;
  asArray: () => Filter[];
}

function readURL(): Record<string, Filter> {
  if (typeof window === "undefined") return {};
  const p = new URLSearchParams(window.location.search);
  const out: Record<string, Filter> = {};
  p.forEach((v, k) => { if (k.startsWith("f.")) out[k.slice(2)] = { field: k.slice(2), op: "eq", value: v }; });
  return out;
}

function writeURL(filters: Record<string, Filter>) {
  if (typeof window === "undefined") return;
  const p = new URLSearchParams(window.location.search);
  [...p.keys()].forEach((k) => k.startsWith("f.") && p.delete(k));
  Object.values(filters).forEach((f) => p.set(`f.${f.field}`, String(f.value)));
  window.history.replaceState(null, "", `${window.location.pathname}?${p.toString()}`);
}

export const useFilters = create<FilterState>((set, get) => ({
  filters: readURL(),
  set: (field, value, op = "eq") =>
    set((s) => {
      const filters = { ...s.filters, [field]: { field, op, value } };
      writeURL(filters);
      return { filters };
    }),
  toggle: (field, value) =>
    set((s) => {
      const cur = s.filters[field];
      const filters = { ...s.filters };
      if (cur && cur.value === value) delete filters[field];
      else filters[field] = { field, op: "eq", value };
      writeURL(filters);
      return { filters };
    }),
  clear: (field) =>
    set((s) => {
      const filters = field ? { ...s.filters } : {};
      if (field) delete filters[field];
      writeURL(filters);
      return { filters };
    }),
  asArray: () => Object.values(get().filters),
}));
