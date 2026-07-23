# yachaydeep-analytics

**Sistema de analítica y visualización de la casa.** Un repo, fuente única, que
convierte **cualquier dato cuantitativo — de cualquier sector** (educación, turismo,
empresa, salud, finanzas…) — en tableros y reportes dinámicos para tomar decisiones.

Se usa de **dos formas**:

1. **Dentro de tus apps** (Core, Áncora, Kullki): se instala por versión, como
   `@yachaydeep/brand`, y vive nativo con la marca de cada producto — no embebido.
2. **En autoservicio** (Studio): alguien **sube su Excel/CSV o conecta una base** y
   obtiene un tablero automáticamente, sin escribir código ni DAX. Base para vender
   suscripciones en `analytics.yachaydeep.com`.

> El motor infiere por la **forma del dato**, no por el negocio: sirve igual para
> matrículas, ocupación hotelera o ventas por región.

## Qué sabe hacer

- **Entiende los datos** (`profile`): infiere el tipo de cada columna y propone métricas + tablero.
- **Elige el gráfico** (`resolver`): forma del dato → gráfico correcto (como "Show Me" de Tableau).
- **Catálogo amplio y accesible**: KPI, línea/área, barras, apiladas, dona, treemap, dispersión,
  histograma, boxplot, heatmap, embudo, **red (VOSviewer)**, **coroplético de Ecuador** — con
  **paleta validada** para daltonismo (claro/oscuro) y cross-highlighting.
- **Relaciones entre tablas, sin DAX** (`model`): detecta las claves foráneas y consulta cruzando
  tablas armando los JOIN solo.
- **Limpia tus Excel** (`ingest`): normaliza encabezados, tipos, montos es-EC, duplicados, vacíos.
- **Pregúntale a tus datos** (`interpret`): lenguaje natural → consulta, con tu LLM (Cerebras/Kimi) o reglas.
- **Editores para no técnicos**: editor visual de relaciones + constructor de tablero (demos).
- **Big data**: pushdown a la base; probado con **1M de filas en DuckDB** (~440 ms). Postgres,
  ClickHouse, BigQuery, Snowflake por DSN.
- **Multi-tenant** (`tenancy`): aislar inquilinos (Core/Áncora/Kullki → suscriptores).
- **Seguridad de PII**: índice ciego, k-anonimato, sin llaves en la capa de analítica (LOPDP).
- **Reportes**: exportar CSV/PNG.

## Tres artefactos (versionados juntos)

| Paquete | Qué es | Instala |
|---|---|---|
| `@yachaydeep/analytics-contract` | El **contrato**: tipos TS + JSON Schema | `npm i @yachaydeep/analytics-contract` |
| `yd-analytics` (Python) | El **cerebro**: motor, resolver, grafos, model, profiler, ingest, assist, tenancy | `pip install "yd-analytics[api]"` |
| `@yachaydeep/dashboard` (React) | La **cara**: `Dashboard`, `Panel`, `NetworkView`, `ChoroplethView` | `npm i @yachaydeep/dashboard` |

## Estructura

```
yachaydeep-analytics/
├── packages/
│   ├── contract/    tipos TS + JSON Schema (generado desde Pydantic)
│   ├── py/          yd-analytics (registry, engine, resolver, graph, model, profiler,
│   │                ingest, assist, tenancy, security, export, router) + tests
│   └── dashboard/   @yachaydeep/dashboard (componentes React/ECharts + paleta validada)
├── examples/
│   ├── studio/          app "sube tus datos → tablero" (FastAPI + UI)  ← autoservicio
│   ├── backend-demo/    app FastAPI mínima que monta make_router
│   ├── vite-app/        app React que consume @yachaydeep/dashboard (nativo)
│   └── standalone-html/ 9 demos autocontenidos (abrir en el navegador)
├── docs/            DASHBOARD · DISTRIBUCION · DESIGN-SYSTEM · VS-POWERBI · SEGURIDAD-DATOS
│                    · ESCALA · MULTI-TENANT · DESPLIEGUE
└── scripts/         gen_schema.py
```

## Empezar

**Modo autoservicio (Studio) — sube datos y obtén tablero:**
```bash
cd examples/studio && pip install -e ../../packages/py[api,ingest] python-multipart uvicorn
uvicorn app:app --reload          # http://127.0.0.1:8000 → sube ejemplo.csv
```

**Cerebro + pruebas:**
```bash
cd packages/py && pip install -e .[dev] && pytest      # 41 pruebas verdes
```

**Cara (React), consumo nativo:**
```bash
npm install && npm run build
npm --workspace example-vite-app run dev
```

**Solo mirar** (`examples/standalone-html/`, sin servidor): `dashboard-demo`,
`powerbi-demo` (cross-highlighting), `graph-demo`, `vosviewer-demo`, `gallery-demo`
(catálogo completo), `ask-demo` («pregúntale a tus datos»), `ingest-demo` (subir/limpiar),
`model-editor-demo` (relaciones tipo Power Pivot), `builder-demo` (constructor de tablero).

## Cómo lo consume una app (Core / Áncora / Kullki)

```python
from yd_analytics import make_router
app.include_router(make_router(get_engine=get_engine, get_role=deps_de_yd_auth))
```
```tsx
import { Dashboard, NetworkView } from "@yachaydeep/dashboard";
<Dashboard spec={miDashboardSpec} />
```
El mismo tablero se ve **ámbar en Áncora y verde en Kullki** sin tocar el paquete.

## Relaciones sin DAX + preguntar

```python
from yd_analytics import build_model, query_related, interpret, openai_compatible_llm
model = build_model(engine, ["ventas", "sucursales", "productos"])   # detecta las relaciones
rows  = query_related(engine, model, fact="ventas", measure="SUM(monto)",
                      dimension="ciudad", dim_table="sucursales")     # el JOIN lo arma solo
llm   = openai_compatible_llm("https://api.cerebras.ai/v1", KEY, "llama-3.3-70b")
sug   = interpret("ventas por ciudad", llm=llm)                      # NL → consulta + gráfico
```

## Documentación

- [`DASHBOARD.md`](docs/DASHBOARD.md) — arquitectura del sistema.
- [`DISTRIBUCION.md`](docs/DISTRIBUCION.md) — paquetes, consumo nativo y gobernanza.
- [`DESIGN-SYSTEM.md`](docs/DESIGN-SYSTEM.md) — tokens, paleta validada, catálogo, accesibilidad.
- [`VS-POWERBI.md`](docs/VS-POWERBI.md) — cómo igualar y superar a Power BI.
- [`SEGURIDAD-DATOS.md`](docs/SEGURIDAD-DATOS.md) — analítica sobre datos cifrados.
- [`ESCALA.md`](docs/ESCALA.md) — big data (pushdown, motores columnares).
- [`MULTI-TENANT.md`](docs/MULTI-TENANT.md) — inquilinos y suscripciones.
- [`DESPLIEGUE.md`](docs/DESPLIEGUE.md) — GitHub + Railway + Vercel, dominio `analytics.yachaydeep.com`.

## Licencia

MIT © 2026 Carlos Vásconez-Paredes — Yachay Deep · *un producto de Yachay Deep*
