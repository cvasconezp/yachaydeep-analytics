/* @yachaydeep-yd/dashboard — Formato canónico es-EC (miles con punto, coma decimal).
   Réplica del formateador de la casa (frontend/src/lib/format.ts). ÚNICO formateador:
   ningún número se imprime sin pasar por aquí. */
const LOCALE = "es-EC";

export function money(value: number): string {
  return new Intl.NumberFormat(LOCALE, {
    style: "currency", currency: "USD", minimumFractionDigits: 2, maximumFractionDigits: 2,
  }).format(value);
}
export function number(value: number, decimals = 0): string {
  return new Intl.NumberFormat(LOCALE, {
    minimumFractionDigits: decimals, maximumFractionDigits: decimals,
  }).format(value);
}
export function percent(value: number, decimals = 1): string {
  return `${number(value, decimals)} %`;
}
export function impact(value: number): string {
  return `${number(value)}+`;
}
