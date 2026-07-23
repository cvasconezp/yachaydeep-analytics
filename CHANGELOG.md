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
- Ejemplos: backend FastAPI, app Vite y cuatro demos HTML autocontenidos.
- Docs: `DASHBOARD.md` (arquitectura) y `DISTRIBUCION.md` (paquetes y consumo).
