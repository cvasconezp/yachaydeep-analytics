/* @yachaydeep/dashboard — Configuración runtime del cliente de analítica.

   Permite fijar, desde la app anfitriona y en tiempo de ejecución, la URL base del
   API, una API key (se envía como cabecera `X-API-Key`) y cabeceras extra. Así el
   mismo bundle sirve para embeber en distintas apps sin recompilar.

   Uso:
     import { configureAnalytics } from "@yachaydeep/dashboard";
     configureAnalytics({ apiBase: "https://analytics.yachaydeep.com", apiKey: "..." });
*/

export interface AnalyticsClientConfig {
  /** URL base del API (sin barra final). Ej.: "https://analytics.yachaydeep.com". */
  apiBase?: string;
  /** API key; si se define, se envía como `X-API-Key`. */
  apiKey?: string;
  /** Cabeceras extra a fusionar en cada petición. */
  headers?: Record<string, string>;
  /** Política de credenciales del fetch. Por defecto: "include" sin apiKey (cookie
   *  de sesión de yd.auth), "omit" cuando hay apiKey (evita choques de CORS). */
  credentials?: RequestCredentials;
}

const DEFAULT_BASE =
  ((import.meta as { env?: { VITE_ANALYTICS_API?: string } }).env?.VITE_ANALYTICS_API) ??
  "http://127.0.0.1:8000";

let _cfg: AnalyticsClientConfig = { apiBase: DEFAULT_BASE };

/** Configura el cliente (fusiona con lo previo). Idempotente. */
export function configureAnalytics(cfg: AnalyticsClientConfig): void {
  _cfg = { ..._cfg, ...cfg };
}

/** URL base efectiva. */
export function analyticsBase(): string {
  return (_cfg.apiBase ?? DEFAULT_BASE).replace(/\/+$/, "");
}

/** Cabeceras efectivas (Content-Type + API key + extras). */
export function analyticsHeaders(): Record<string, string> {
  const h: Record<string, string> = { "Content-Type": "application/json", ...(_cfg.headers ?? {}) };
  if (_cfg.apiKey) h["X-API-Key"] = _cfg.apiKey;
  return h;
}

/** Política de credenciales efectiva. */
export function analyticsCredentials(): RequestCredentials {
  return _cfg.credentials ?? (_cfg.apiKey ? "omit" : "include");
}
