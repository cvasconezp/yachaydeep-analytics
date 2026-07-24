/* @yachaydeep-yd/dashboard — Paleta y tokens de gráfico (sistema de diseño).

   Construido con el método de la skill `dataviz`: el color se COMPUTA, no se estima.
   La paleta categórica de la casa se validó con scripts/validate_palette.js —
   pasa banda de luminosidad, piso de croma, separación CVD y contraste en claro y
   oscuro. NO usa violeta (reservado a terceros por la marca).

   Resultado del validador (categórica, 7 slots):
     light: worst adjacent CVD ΔE 7.2 (banda 6–8 → exige encoding secundario:
            leyenda + etiquetas directas), normal-vision 19.6, contraste con relief
            en aqua/amarillo/magenta (etiquetas visibles o vista tabla).
     dark:  todos los checks PASS.
   Tope para dispersión/mapa (all-pairs): los 3 primeros slots. Pasado ahí → "Otros".
*/

export type Mode = "light" | "dark";

/** Paleta categórica validada (identidad de serie). Orden FIJO, nunca ciclado. */
export const CATEGORICAL: Record<Mode, string[]> = {
  light: ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#e34948"],
  dark:  ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#e66767"],
};

/** Tope de series para gráficos de todos-los-pares (scatter, burbuja, mapa). */
export const ALL_PAIRS_CAP = 3;

/** Rampa secuencial (magnitud): un solo tono, claro→oscuro. Heatmaps, coropléticos. */
export const SEQUENTIAL = [
  "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b",
];

/** Diverging: dos polos + gris neutro al centro. */
export const DIVERGING = { low: "#2a78d6", mid: { light: "#f0efec", dark: "#383835" }, high: "#e34948" };

/** Estados (reservados; nunca como "serie 4"; van con icono + etiqueta). */
export const STATUS = { good: "#0ca30c", warning: "#fab219", serious: "#ec835a", critical: "#d03b3b" };

/** Cromo e ink del gráfico por modo. */
export const CHROME: Record<Mode, {
  surface: string; page: string; ink: string; ink2: string; muted: string; grid: string; axis: string;
}> = {
  light: { surface: "#fcfcfb", page: "#f9f9f7", ink: "#0b0b0b", ink2: "#52514e", muted: "#898781", grid: "#e1e0d9", axis: "#c3c2b7" },
  dark:  { surface: "#16181d", page: "#0d0d0d", ink: "#ffffff", ink2: "#c3c2b7", muted: "#898781", grid: "#2c2c2a", axis: "#383835" },
};

/** Color primario del PRODUCTO (serie única, KPIs). Se sobreescribe por marca:
    Áncora ámbar, Kullki verde, Core dorado. Aquí el navy institucional por defecto. */
export const PRODUCT_PRIMARY = { light: "#1B3A6B", dark: "#3987e5", accent: "#E8A838" };

export function categorical(mode: Mode = "light"): string[] { return CATEGORICAL[mode]; }
export function seriesColor(i: number, mode: Mode = "light"): string {
  const p = CATEGORICAL[mode];
  return p[i % p.length]; // el 8.º NO se genera: se pliega a "Otros" aguas arriba
}
