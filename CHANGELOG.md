# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/);
versionado SemVer. El contrato manda: un cambio incompatible es *major*.

## [0.1.0] — 2026-07 · inicial

### Añadido
- **@yachaydeep/analytics-contract** — tipos TS + JSON Schema (generado desde Pydantic).
- **yd-analytics** (Python) — motor tabular (`run_query`), grafos (`run_graph`),
  resolver forma→gráfico, SQL seguro con whitelist, caché versionada, autorización
  por rol, **profiler** de auto-perfilado y factoría `make_router`.
- **@yachaydeep/dashboard** (React) — `Dashboard`, `Panel`, `NetworkView`
  (estilo VOSviewer, modos *cluster* y *overlay*), hooks y formateador es-EC.
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
