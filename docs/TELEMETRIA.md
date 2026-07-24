# TELEMETRÍA — Analítica de producto (uso de tus apps)

Yachay Deep Analytics no solo analiza los datos que cargas: también mide el **uso
de tus propias apps** (Core, Áncora, Kullki y otras). Cuántas personas entran, a
qué pantallas/espacios van y desde qué dispositivo — y lo hace con el **mismo
motor**: los eventos aterrizan en la tabla `eventos_uso` y se perfilan como
cualquier otra tabla. La app se analiza a sí misma; no hace falta una herramienta
aparte tipo Google Analytics.

## Cómo funciona

```
   app de la casa            Yachay Deep Analytics
  ┌───────────────┐  eventos  ┌───────────────────────────┐
  │ yd-telemetry  │ ───────▶  │ POST /telemetry/collect    │
  │  (navegador)  │           │   → record_events()        │
  └───────────────┘           │   → tabla eventos_uso       │
                              │   → métricas uso_* (motor)  │
                              └───────────────────────────┘
                                        │
                                 /analytics/query  → tablero de uso
```

## 1. Instrumenta una app (una línea)

Pega el script en cada app de la casa. Con atributos `data-*` se auto-inicializa
y emite un `pageview` en cada carga y cambio de ruta (SPA):

```html
<script src="https://analytics.yachaydeep.com/yd-telemetry.js"
        data-endpoint="https://yachay-deep-analytics-production.up.railway.app/telemetry/collect"
        data-producto="core"></script>
```

Eventos a medida:

```js
ydTelemetry.track("click", { boton: "exportar" });
ydTelemetry.pageview("/core/riesgo");
```

O por API, pasando el **seudónimo** del usuario logueado (su hash, nunca PII):

```js
ydTelemetry.init({
  endpoint: "…/telemetry/collect",
  producto: "kullki",
  usuarioId: hashDelSocio,   // p. ej. HMAC(cédula) — el texto plano NO viaja
});
```

## 2. Qué se guarda (sin PII)

Tabla `eventos_uso`: `producto`, `evento`, `pantalla`, `usuario_id` (seudónimo),
`sesion_id`, `dispositivo`, `os`, `pais`, `dia`, `ts`. **Nunca** cédula, correo ni
nombre. El cliente deriva dispositivo/OS del navegador y genera un anon-id si no
le pasas uno.

## 3. Consulta el uso (métricas `uso_*`)

Al arrancar, el backend hace `telemetry.ensure_events_table()` y
`telemetry.register_telemetry()`, dejando estas métricas listas para
`/analytics/query`:

| Métrica | Qué responde |
|---|---|
| `uso_usuarios_activos` | Personas distintas (DAU/WAU según el rango) |
| `uso_usuarios_por_dia` | Serie de usuarios activos por día |
| `uso_sesiones` | Sesiones iniciadas |
| `uso_eventos` | Total de eventos |
| `uso_top_pantallas` | A qué espacios van (dim `pantalla`) |
| `uso_por_dispositivo` | Desde qué dispositivo (dim `dispositivo`) |
| `uso_por_producto` | Reparto entre Core/Áncora/Kullki (dim `producto`) |

Ejemplo (usuarios activos por día):

```json
POST /analytics/query
{ "metric": "uso_usuarios_por_dia", "dimensions": ["dia"] }
```

## 4. Privacidad (LOPDP)

- `usuario_id` seudonimizado en origen; el paquete nunca ve PII ni guarda llaves.
- Las métricas que **cuentan personas** usan supresión **k-anónima** (k=5): no se
  muestran grupos con menos de 5 personas, para no re-identificar.
- Todo vive en **tu** Postgres, por inquilino (ver `MULTI-TENANT.md`).

## 5. Demo

`examples/standalone-html/telemetry-demo.html` — tablero de uso con datos de
muestra (DAU, pantallas, dispositivos, reparto por producto). Cliente:
`examples/standalone-html/yd-telemetry.js`. Endpoint: `examples/studio/app.py`
(`POST /telemetry/collect`). Módulo y contrato: `yd_analytics/telemetry.py`.

---

*Yachay Deep · Telemetría v0.1 · Julio 2026.*
