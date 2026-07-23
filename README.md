# yachaydeep-analytics

**Sistema de representación gráfica de la casa.** Un repo, fuente única, que Core,
Áncora y Kullki **consumen por versión** — como `@yachaydeep/brand`, pero para datos:
lee los datos disponibles, los interpreta y genera gráficas dinámicas para la toma de
decisiones. Vive **dentro** de cada app (nativo, no embebido).

> Convierte datos en decisiones. En el aula, en la empresa y en la comunidad.

## Tres artefactos (versionados juntos)

| Paquete | Qué es | Instala |
|---|---|---|
| **`@yachaydeep/analytics-contract`** | El **contrato**: tipos TS + JSON Schema. El pegamento que evita desincronización. | `npm i @yachaydeep/analytics-contract` |
| **`yd-analytics`** (Python) | El **cerebro**: motor, resolver forma→gráfico, grafos, profiler, seguridad, router. | `pip install "yd-analytics[api]"` |
| **`@yachaydeep/dashboard`** (React) | La **cara**: `Dashboard`, `Panel`, `NetworkView` (estilo VOSviewer). | `npm i @yachaydeep/dashboard` |

## Estructura

```
yachaydeep-analytics/
├── packages/
│   ├── contract/      @yachaydeep/analytics-contract  (tipos TS + schema JSON)
│   ├── py/            yd-analytics  (registry, engine, resolver, graph, profiler, router)
│   └── dashboard/     @yachaydeep/dashboard  (Dashboard, Panel, NetworkView, hooks)
├── examples/
│   ├── backend-demo/  app FastAPI que monta make_router
│   ├── vite-app/      app React que consume @yachaydeep/dashboard (nativo)
│   └── standalone-html/  cuatro demos autocontenidos (abrir en el navegador)
├── docs/              DASHBOARD.md (arquitectura) · DISTRIBUCION.md (paquetes y consumo)
└── scripts/           gen_schema.py (JSON Schema desde los modelos Pydantic)
```

## Empezar en 2 minutos

**Cerebro + backend de ejemplo:**

```bash
cd packages/py && pip install -e .[dev] && pytest        # 16 pruebas verdes
cd ../../examples/backend-demo
python seed_demo.py && python seed_graph.py
uvicorn app:app --reload                                  # http://127.0.0.1:8000/docs
```

**Cara (React), consumo nativo:**

```bash
npm install && npm run build          # compila contract + dashboard
npm --workspace example-vite-app run dev
```

**Solo mirar:** abre cualquier archivo de `examples/standalone-html/`
(`dashboard-demo`, `powerbi-demo`, `graph-demo`, `vosviewer-demo`, **`gallery-demo`**,
**`ask-demo`**) — traen ECharts incrustado y corren sin servidor. `gallery-demo`
muestra todo el catálogo con la paleta validada en claro/oscuro; `ask-demo` es el
buscador «pregúntale a tus datos».

## Cómo lo consume una app (Core / Áncora / Kullki)

```python
# backend (FastAPI de la app)
from yd_analytics import make_router
app.include_router(make_router(get_engine=get_engine, get_role=deps_de_yd_auth))
```

```tsx
// frontend (rutas propias de la app, con sus tokens de marca)
import { Dashboard, NetworkView } from "@yachaydeep/dashboard";
<Dashboard spec={miDashboardSpec} />
<NetworkView data={red} colorBy="overlay" />
```

El mismo tablero se ve **ámbar en Áncora y verde en Kullki** sin tocar el paquete.

## Analiza los datos y propone el tablero (profiler)

```python
from yd_analytics import profile
p = profile(engine, "evaluacion_riesgo")
p.columns     # tipo semántico de cada campo (temporal, categórico, numérico, id…)
p.metrics     # métricas candidatas (conteo, promedios…)
p.dashboard   # DashboardSpec inicial, listo para revisar y afinar
```

## ¿Tienes Excel? Ingesta + limpieza en un paso

```python
from yd_analytics import ingest          # requiere el extra [ingest] (pandas)
rep = ingest("aportes.xlsx", engine, "aportes")
rep.issues     # ["encabezados normalizados", "3 duplicados eliminados", …]
rep.columns    # tipos inferidos de cada columna ya limpia
rep.profile    # métricas y DashboardSpec propuestos sobre los datos limpios
```

Lee Excel/CSV, normaliza encabezados y tipos (incluye montos es-EC), quita vacíos y
duplicados, carga a la BD y perfila — listo para graficar.

## Pregúntale a tus datos (asistencia)

```python
from yd_analytics import interpret, openai_compatible_llm
llm = openai_compatible_llm("https://api.cerebras.ai/v1", KEY, "llama-3.3-70b")  # o Kimi
sug = interpret("¿riesgo por carrera?", llm=llm)   # → MetricQuery + gráfico sugerido
```

Endpoint listo: `POST /analytics/assist {"question": "..."}`. Sin LLM usa reglas offline.

## Documentación

- [`docs/DASHBOARD.md`](docs/DASHBOARD.md) — arquitectura del sistema (capas, contratos, resolver).
- [`docs/DISTRIBUCION.md`](docs/DISTRIBUCION.md) — modelo de paquetes, consumo nativo y gobernanza.
- [`docs/DESIGN-SYSTEM.md`](docs/DESIGN-SYSTEM.md) — tokens, paleta validada, catálogo de gráficos, estados y accesibilidad.

## Licencia

MIT © 2026 Carlos Vásconez-Paredes — Yachay Deep · *un producto de Yachay Deep*
