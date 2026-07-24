# Integrar Yachay Deep Analytics en tu app (10 minutos)

Guía para embeber tableros de **Yachay Deep Analytics** dentro de una app React
(Core, Áncora, Kullki o cualquier app tuya). Dos piezas: el **paquete de la cara**
(`@yachaydeep/dashboard`) y el **API con estadística real** (el Studio / backend).

> Versión de los paquetes: `0.2.0`. El contrato (`@yachaydeep/analytics-contract`)
> es la superficie pública; fija una versión y actualiza a conciencia.

---

## 1. Instala el paquete y sus dependencias

```bash
npm install @yachaydeep/dashboard @yachaydeep/analytics-contract
# dependencias peer (si aún no están en tu app):
npm install react echarts echarts-for-react zustand @tanstack/react-query
```

## 2. Configura el cliente (URL del API + API key)

En el arranque de tu app, una sola vez:

```ts
import { configureAnalytics } from "@yachaydeep/dashboard";

configureAnalytics({
  apiBase: "https://analytics.yachaydeep.com",   // tu backend
  apiKey: import.meta.env.VITE_YD_API_KEY,        // NUNCA la quemes en el bundle público
});
```

Con `apiKey` definido, cada petición envía la cabecera `X-API-Key` y usa
`credentials: "omit"` (evita choques de CORS). Si en cambio usas la sesión de
`yd.auth` (cookie) en el mismo dominio, omite `apiKey` y se usará `credentials: "include"`.

## 3. Renderiza un tablero

```tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Dashboard } from "@yachaydeep/dashboard";
import "@yachaydeep/dashboard/dist/style.css"; // si tu bundler lo requiere

const qc = new QueryClient();

const spec = {
  titulo: "Ventas 2026",
  paneles: [
    { id: "kpi",  metric: "ventas_totales", chartHint: "kpi", size: "sm" },
    { id: "serie", metric: "ventas", dimensions: ["mes"], size: "lg" },
    { id: "reg",  metric: "ventas", dimensions: ["region"], size: "md" },
  ],
};

export function MiTablero() {
  return (
    <QueryClientProvider client={qc}>
      <Dashboard spec={spec} />
    </QueryClientProvider>
  );
}
```

El `spec` es el **DashboardSpec** declarativo (el mismo JSON que exporta el
constructor sin código). Cada panel consulta su métrica en el backend; el clic en
una barra filtra todo el tablero (cross-filtering) vía el store compartido.

## 4. Backend: cierra el API antes de producción

El API arranca **abierto** en desarrollo. Para producción, define variables de entorno:

| Variable | Ejemplo | Efecto |
|---|---|---|
| `YD_API_KEYS` | `clave1:acme:admin,clave2:beta:viewer` | Cierra el API. Formato `clave:tenant:rol`. |
| `YD_ALLOWED_ORIGINS` | `https://miapp.com,https://admin.miapp.com` | Restringe CORS a esos orígenes. |
| `YD_REQUIRE_AUTH` | `1` | Fuerza el cierre aunque no hayas puesto llaves (rechaza todo). |
| `ANALYTICS_DB_URL` | `postgresql://…` | Base de datos del backend. |

Con `YD_API_KEYS` definido:

- `/health` queda abierto (para health checks).
- `/analytics/query`, `/analytics/stats`, `/report`, `/ingest`, `/telemetry/collect`
  exigen una llave válida (`X-API-Key` o `Authorization: Bearer <clave>`), o responden
  **401** (falta llave) / **403** (llave inválida).
- La llave define el **rol** con el que se filtran las métricas y el **tenant**
  (aislamiento de datos multi-inquilino).

Prueba rápida:

```bash
curl -s https://analytics.yachaydeep.com/analytics/query \
  -H "X-API-Key: clave1" -H "Content-Type: application/json" \
  -d '{"metric":"ventas","dimensions":["mes"]}'
```

## 5. Tematiza (opcional)

La paleta y el formateo son accesibles (validados para daltonismo) y se exportan:

```ts
import { palette, format } from "@yachaydeep/dashboard";
```

La identidad visual (color, tipografía) vive en `@yachaydeep/brand`; no edites
colores directamente en el consumidor.

---

## Notas de seguridad

- **Nunca** publiques una API key con rol `admin` en un bundle de navegador público.
  Para apps públicas, usa una llave de rol limitado (p. ej. `viewer`) por tenant, o
  proxea las consultas desde tu backend.
- Rota las llaves cambiando `YD_API_KEYS` y redeployando.
- El backend seudonimiza los `usuario_id` de telemetría y no guarda PII.
