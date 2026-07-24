# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/);
versionado SemVer. El contrato manda: un cambio incompatible es *major*.

## [0.3.0] — 2026-07 · firma de atribución

### Añadido
- **@yachaydeep-yd/dashboard**: componente `AttributionBadge` — firma
  "Yachay Deep Analytics" en cursiva, esquina inferior derecha, con una franja de
  acento. Auto-contenido (estilos en línea). La franja **adopta el color de la
  página anfitriona** vía la variable CSS `--yd-accent` (o prop `attributionAccent`);
  si no se define, usa el **cian propio de Analytics** (`#0E9AB8`, familia hielo/datos).
  `<Dashboard attribution={false}>` la oculta (pensado para planes de pago).
- Merge del piloto **Core "Vista General"** (`yd_analytics/apps/core.py`): declara
  las tarjetas del Análisis Institucional como MetricSpecs con el mismo SQL (11 tests).

## [0.2.0] — 2026-07 · embebible en producción

### Añadido
- **Autenticación por API key** (`yd_analytics.auth`): dependencias FastAPI
  `make_auth` que validan la llave en **tiempo constante** y resuelven tenant/rol.
  Modo abierto en desarrollo; cerrado con `YD_API_KEYS` / `YD_REQUIRE_AUTH`.
- **Studio** cierra sus endpoints de datos (`/analytics/*`, `/report`, `/ingest`,
  `/telemetry/collect`) y restringe CORS con `YD_ALLOWED_ORIGINS`.
- **@yachaydeep-yd/dashboard**: `configureAnalytics({ apiBase, apiKey })` — configura
  la URL base y la API key en runtime (cabecera `X-API-Key`), para embeber el mismo
  bundle en distintas apps sin recompilar.
- **docs/INTEGRACION.md**: guía de integración de 10 minutos.
- **Auditoría de exactitud** (`packages/py/audit_stats.py`): 74 verificaciones
  cruzadas contra statsmodels / pymannkendall / scipy — 0 discrepancias.

### Cambiado
- Paquetes a `0.2.0`; `publishConfig.access = public` y metadata de publicación.
- Se eliminan las referencias rezagadas a "VOSviewer" en el paquete y su README.

## [0.1.0] — 2026-07 · inicial

### Añadido
- **@yachaydeep-yd/analytics-contract** — tipos TS + JSON Schema (generado desde Pydantic).
- **yd-analytics** (Python) — motor tabular (`run_query`), grafos (`run_graph`),
  resolver forma→gráfico, SQL seguro con whitelist, caché versionada, autorización
  por rol, **profiler** de auto-perfilado y factoría `make_router`.
- **@yachaydeep-yd/dashboard** (React) — `Dashboard`, `Panel`, `NetworkView`
  (redes, modos *cluster* y *overlay*), hooks y formateador es-EC.
- **Sistema de diseño de gráficos**: paleta categórica **validada** con
  `scripts/validate_palette.js` (sin violeta, segura para daltonismo en claro y
  oscuro), `palette.ts`, y catálogo ampliado en `chartOptions.ts` (dona, apiladas,
  treemap, dispersión, histograma, embudo). Resolver ampliado a las formas
  `part_to_whole`, `distribution`, `correlation`, `funnel` (+ `ChartType` con
  `pie`/`histogram`/`boxplot`). Guiado por las skills `dataviz` y `design-system`.
- Ejemplos: backend FastAPI, app Vite y **cinco** demos HTML autocontenidos
  (incluye `gallery-demo` con todo el catálogo en claro/oscuro).
- Docs: `DASHBOARD.md` (arquitectura), `DISTRIBUCION.md` (paquetes y consumo) y
  `DESIGN-SYSTEM.md` (tokens, paleta validada, catálogo, estados, accesibilidad).
- **Capa de asistencia** (`interpret`): pregunta en lenguaje natural → MetricQuery +
  gráfico, con fallback por reglas offline y adaptador `openai_compatible_llm`
  (Cerebras, Kimi/Moonshot, OpenAI — solo cambia base_url/model).
- **Seguridad de datos cifrados**: índice ciego en `MetricSpec`/SQL, supresión
  k-anónima, hook `decrypt_labels` (el paquete nunca tiene las llaves) y detección de
  columnas cifradas en el profiler. Doc `SEGURIDAD-DATOS.md`.
- **Exportación**: `to_csv` (Python) y `exportCSV`/`exportPNG` (frontend).
- **Mapa coroplético de Ecuador** (`ChoroplethView` + GeoJSON de provincias) y el
  clúster VOSviewer, ambos integrados en `gallery-demo`.
- `registry.register()` para que las apps añadan sus métricas.
- **Ingesta de Excel/CSV** (`ingest`, extra `[ingest]`): limpia y normaliza
  (encabezados, tipos, montos es-EC, duplicados, vacíos), carga y perfila. Con test.
- **Buscador de lenguaje natural**: endpoint `POST /analytics/assist` (usa `assist_llm`
  como Cerebras/Kimi o reglas offline) y demo `ask-demo.html`.
- `MetricSpec.param_defaults` (valores por defecto de la medida, p. ej. `umbral`).
- **Modelo semántico automático** (`model`): detecta relaciones entre tablas (claves
  foráneas por nombre/unicidad) y `query_related` consulta cruzando tablas armando los
  JOIN solo — **sin DAX ni Power Pivot**. Con tests.
- Demos: `ingest-demo.html` (asistente visual de subida/limpieza) y cableado de
  `ask-demo` al backend (`/analytics/assist`). Doc `VS-POWERBI.md`.
- **Editor visual de relaciones** (`model-editor-demo.html`) y **constructor de tablero
  sin código** (`builder-demo.html`) — las dos piezas para usuarios no técnicos.
- **Big data**: prueba del motor contra **DuckDB** (columnar) con cientos de miles de
  filas por pushdown (`tests/test_bigdata.py`, extra `[bigdata]`). Doc `ESCALA.md`.
- **Studio** (`examples/studio`): app autoservicio "sube tu Excel/CSV → tablero"
  (FastAPI + UI), verificada de punta a punta.
- **Multi-tenant** (`tenancy`): `TenantResolver`, resolución por subdominio
  (`tenant_from_host`), aislamiento por Engine y `row_filter`. Con tests. Doc
  `MULTI-TENANT.md`.
- Docs de despliegue (`DESPLIEGUE.md`: GitHub + Railway + Vercel) y README reescrito
  (sector-agnóstico, dos modos). El sistema analiza **cualquier dato cuantitativo de
  cualquier sector**.
