# DASHBOARD — Arquitectura de tableros dinámicos de la casa (`yd-analytics`)

> **Módulo compartido de casa.** Igual que `yd-auth` o `yd-crypto`, este es un capability
> que los productos **consumen**, no reimplementan. Un tablero nuevo en Core, Kullki, Horario
> Inteligente o cualquier producto se monta declarando métricas y paneles, no escribiendo
> gráficos a mano. Si el módulo evoluciona, se hace en el paquete compartido, no en el consumidor.

**Versión:** 0.1 (borrador de arquitectura) · Julio 2026 · Cayambe, Ecuador
**Depende de:** `docs/METRICS.md`, `docs/DATA_DICTIONARY.md`, baseline de seguridad (`yd/`), `frontend/src/lib/format.ts`
**Alcance de este documento:** define **cómo** se leen los datos, se interpretan y se convierten en
gráficas predeterminadas, interactivas y coherentes con la marca. No es un producto: es la base
reutilizable para montar tableros en distintas web apps de la casa.

---

## 0. Principio rector

Un tablero de casa no se **dibuja**, se **declara**. El desarrollador dice *qué métrica* quiere ver;
el sistema decide *cómo* graficarla a partir de la forma de esa métrica, la pinta con los tokens de
marca y la conecta al resto del tablero para que todo reaccione a cada clic. La cadena que da la
"solvencia tipo Power BI" es siempre la misma:

```
datos (PostgreSQL) → motor de métricas (backend) → resultado normalizado + forma
      → resolver de gráficos → especificación de gráfico → runtime interactivo (front)
```

Tres reglas de casa que este módulo hace cumplir por diseño:

1. **Ninguna métrica de dominio se calcula en el frontend** (METRICS.md). El motor vive en el backend.
2. **El `DATA_DICTIONARY` es la fuente de verdad.** Si una métrica no está declarada ahí, no se grafica.
3. **Un solo formateador es-EC** (`format.ts`). Ningún número se imprime sin pasar por él.

---

## 1. Vista general de capas

```
┌──────────────────────────────────────────────────────────────────────────┐
│  FRONTEND  ·  @yachaydeep/dashboard  (React + Vite + ECharts)              │
│                                                                            │
│   DashboardSpec ──► DashboardRuntime ──► Panel[] ──► ChartRenderer(ECharts)│
│                          │   ▲                                             │
│                     FilterStore (cross-filter + drill + estado en URL)     │
│                          │   │  useMetric(metricId, filtros)               │
└──────────────────────────┼───┼────────────────────────────────────────────┘
                           ▼   │  HTTP (contrato tipado)
┌──────────────────────────┼───┼────────────────────────────────────────────┐
│  BACKEND  ·  yd/analytics │   │  (FastAPI, se enciende con ENABLE_ANALYTICS)│
│                           ▼   │                                            │
│   Router /analytics ──► MetricEngine ──► Registry (lee DATA_DICTIONARY)    │
│                             │  │  └─► ChartResolver (forma → ChartSpec)     │
│                             │  └────► Cache (Redis, clave=métrica+filtros+v)│
│                             ▼                                              │
│                       SQL Builder ──► Postgres (réplica de lectura)        │
│                                        └─► vistas materializadas (rollups) │
└────────────────────────────────────────────────────────────────────────────┘
      Seguridad transversal: yd.auth (rol) · yd.security (perímetro) · RLS por métrica
```

| Capa | Dónde vive | Responsabilidad única |
|---|---|---|
| **Fuente** | PostgreSQL de casa (+ réplica de lectura, vistas materializadas) | Guardar los datos; servir agregados rápido sin tocar la carga transaccional |
| **Registro** (`registry.py`) | `backend/yd/analytics/` | Cargar y validar las métricas declaradas (evolución máquina-legible del `DATA_DICTIONARY`) |
| **Motor de métricas** (`engine.py`) | `backend/yd/analytics/` | Resolver una `MetricQuery` → SQL → ejecutar → devolver `MetricResult` normalizado + forma |
| **Resolver de gráficos** (`resolver.py`) | `backend/yd/analytics/` | Interpretar la forma de la métrica y elegir el gráfico predeterminado (`ChartSpec`) |
| **Caché** (`cache.py`) | `backend/yd/analytics/` | Cachear resultados por (métrica + filtros + versión); invalidar por cadencia |
| **Runtime de tablero** | `@yachaydeep/dashboard` (front) | Renderizar paneles, manejar filtros compartidos, drill e interacción |
| **Contrato** | `app/routers/analytics.py` + tipos TS | La frontera HTTP tipada entre front y back |

> **Por qué esta separación.** El resolver de gráficos puede vivir en el backend (elige la
> `ChartSpec`) o en el front (interpreta la forma que devuelve el motor). Recomendamos el resolver
> **en backend** para que la decisión "qué gráfico" sea única y auditable como el resto de las
> métricas; el front solo obedece la `ChartSpec`. Así dos apps distintas grafican la misma métrica
> igual, sin re-decidir.

---

## 2. La pieza central: del dato a la gráfica automática

El requisito clave —"leer los datos, interpretarlos y generar gráficas predeterminadas"— se resuelve
con **dos artefactos**: la **forma semántica** de cada métrica y el **resolver** que la traduce a un
gráfico. Es la misma idea que "Show Me" de Tableau, pero **determinista y propiedad de la casa**: la
misma forma produce siempre el mismo gráfico.

### 2.1 Forma semántica de una métrica

Cada métrica declara, además de su definición del `DATA_DICTIONARY`, su **forma**: cuántas medidas
tiene, sobre qué dimensiones se desglosa y de qué tipo son esas dimensiones (temporal, categórica,
geográfica). El motor detecta la forma efectiva según la consulta (qué dimensiones pidió el panel) y
el resolver decide el gráfico.

| Forma (`shape`) | Composición | Gráfico predeterminado | Alternativa / regla |
|---|---|---|---|
| `scalar` | 1 medida, 0 dimensiones | **Tarjeta KPI** (número grande) + delta vs período previo + sparkline | — |
| `timeseries` | 1 medida × 1 dim. temporal | **Línea** (área si es acumulado/volumen) | > 500 puntos → downsample declarado |
| `category` | 1 medida × 1 dim. categórica (baja cardinalidad ≤ 8) | **Barras verticales** | Ordenar por valor desc. salvo orden natural |
| `category_wide` | 1 medida × 1 dim. categórica (alta cardinalidad) | **Barras horizontales Top-N** + "Otros" | N por defecto 10; el resto se agrupa y se rotula |
| `part_to_whole` | 1 medida que suma un total, ≤ 5 categorías | **Barras apiladas 100%** o **treemap** | Pie/dona **solo** si ≤ 4 categorías |
| `timeseries_multi` | 1 medida × temporal × 1 categórica | **Líneas múltiples** (área apilada si es composición) | Máx. ~6 series visibles; resto en "Otros" |
| `distribution` | 1 medida, muchas observaciones | **Histograma** (o boxplot si se comparan grupos) | — |
| `correlation` | 2 medidas | **Dispersión** (scatter); 3ª medida → tamaño de burbuja | — |
| `matrix` | 1 medida × 2 dim. categóricas | **Mapa de calor** (heatmap) o tabla pivote | Heatmap si ambas ≤ 20 valores |
| `funnel` | Uso: pasos secuenciales | **Embudo** (funnel) | Etiquetar conversión entre pasos |
| `geo` | 1 medida × territorio (provincia/cantón EC) | **Mapa coroplético** (fase posterior) | Requiere topojson de Ecuador |
| `table` | N medidas × N dimensiones (detalle) | **Tabla interactiva** (orden, búsqueda, paginación server-side) | Último recurso; nunca volcar filas crudas de PII |

> **Regla de honestidad (voz de casa).** Si el resolver recorta datos (Top-N, downsample, muestreo),
> el panel **lo dice** ("mostrando 10 de 234; resto agrupado en Otros"). Nunca truncar en silencio:
> un gráfico que oculta que recortó miente por omisión.

### 2.2 Cómo elige el resolver (árbol de decisión)

```
¿cuántas dimensiones pidió el panel?
├─ 0 dimensiones ─────────────► scalar → Tarjeta KPI
├─ 1 dimensión
│   ├─ temporal ─────────────► timeseries → Línea/Área
│   └─ categórica
│        ├─ card. ≤ 8 ───────► category → Barras verticales
│        ├─ suma = total ────► part_to_whole → Barras apiladas / treemap
│        └─ card. > 8 ───────► category_wide → Barras horizontales Top-N
├─ 2 dimensiones
│   ├─ temporal + categórica ► timeseries_multi → Líneas múltiples
│   └─ categórica × categórica► matrix → Heatmap
└─ 2+ medidas sin dimensión ─► correlation → Dispersión
```

El resolver también fija las **interacciones por defecto** de cada gráfico (§4): qué emite al hacer
clic, qué campos van al tooltip, y si permite drill.

### 2.3 Override explícito

El resolver da el **default correcto**, no una camisa de fuerza. Un panel puede forzar su gráfico
(`chartHint: "area"`) cuando el autor sabe algo que la forma no captura. El override se registra en
el `DashboardSpec`, no se improvisa en el componente.

---

## 3. Contratos (la frontera tipada)

Cuatro objetos JSON gobiernan todo. Son el contrato entre capas y la unidad de versionado.

### 3.1 `MetricSpec` — la métrica declarada (extiende el `DATA_DICTIONARY`)

```jsonc
{
  "id": "estudiantes_en_riesgo",
  "clase": "dominio",                     // uso | dominio | impacto (METRICS.md)
  "titulo": "Estudiantes en riesgo",
  "descripcion": "Estudiantes con probabilidad de deserción ≥ umbral en el periodo",
  "shape": "category",                    // forma semántica (§2.1)
  "unidad": "conteo",                     // conteo | moneda | porcentaje | ratio | duracion
  "formato": "number",                    // mapea a format.ts: number|money|percent|impact
  "grano": ["periodo", "carrera", "paralelo"],   // dimensiones disponibles para desglose
  "dim_temporal": "periodo",
  "medida": { "sql": "COUNT(DISTINCT s.id) FILTER (WHERE r.score >= :umbral)" },
  "fuente": "vw_riesgo_estudiante",       // vista/tabla; nunca SELECT * de tablas con PII cruda
  "cadencia": "on-read",                  // on-read | hourly | daily (define caché e invalidación)
  "modelo": { "nombre": "early_warning", "version": "v3" },   // trazabilidad ML (METRICS.md)
  "roles": ["docente", "coordinador", "admin"],   // quién puede verla (§5)
  "version": "v2"
}
```

> El objetivo de casa (MODULES.md) es que el `DATA_DICTIONARY.md` **genere** estos specs, no que se
> mantengan por separado. El diccionario deja de ser solo documentación y pasa a ser el registro que
> alimenta el motor: una sola fuente, versionada, auditable.

### 3.2 `MetricQuery` — lo que pide un panel (request)

```jsonc
{
  "metric": "estudiantes_en_riesgo",
  "dimensions": ["carrera"],              // desglose pedido → determina la forma efectiva
  "grain": "periodo",                     // granularidad temporal si aplica
  "filters": [                            // filtros compartidos del tablero (cross-filter)
    { "field": "periodo", "op": "eq", "value": "2026-1" },
    { "field": "jornada", "op": "in", "value": ["matutina", "nocturna"] }
  ],
  "params": { "umbral": 0.7 },
  "limit": 10
}
```

### 3.3 `MetricResult` — lo que devuelve el motor (response)

Formato **largo/tidy** (una fila por combinación dimensión×valor), fácil de mapear a cualquier gráfico:

```jsonc
{
  "metric": "estudiantes_en_riesgo",
  "shape": "category",                    // forma efectiva resuelta por el motor
  "unidad": "conteo",
  "formato": "number",
  "columns": ["carrera", "valor"],
  "rows": [
    { "carrera": "Software", "valor": 42 },
    { "carrera": "Educación", "valor": 28 }
  ],
  "meta": {
    "version": "v2", "modelo": "early_warning@v3",
    "cached": true, "generated_at": "2026-07-23T10:12:00-05:00",
    "truncated": { "shown": 10, "total": 23, "grouped_as": "Otros" }   // honestidad (§2.1)
  }
}
```

### 3.4 `ChartSpec` — cómo pintarla (lo produce el resolver)

```jsonc
{
  "type": "bar",                          // bar|line|area|scatter|heatmap|funnel|kpi|table|treemap
  "encoding": {
    "x": { "field": "carrera", "type": "nominal" },
    "y": { "field": "valor", "type": "quantitative", "format": "number" }
  },
  "interactions": {
    "emitsFilter": { "field": "carrera" },   // clic → filtra el resto del tablero
    "drilldown": ["carrera", "paralelo"],    // jerarquía de profundización
    "tooltip": ["carrera", "valor"]
  },
  "brand": { "series": "primary" }         // usa --brand-primary; NUNCA violeta (§ marca)
}
```

### 3.5 `DashboardSpec` — el tablero completo

```jsonc
{
  "id": "core-early-warning",
  "titulo": "Alerta temprana — Core",
  "filtros_globales": ["periodo", "carrera", "jornada"],
  "layout": "grid",                       // react-grid-layout
  "paneles": [
    { "id": "kpi1", "metric": "estudiantes_en_riesgo", "size": "sm" },
    { "id": "serie", "metric": "riesgo_promedio", "dimensions": [], "grain": "periodo", "size": "lg" },
    { "id": "porcarrera", "metric": "estudiantes_en_riesgo", "dimensions": ["carrera"],
      "chartHint": null, "size": "md" }
  ]
}
```

Un producto monta un tablero nuevo **escribiendo este JSON**, no componentes. Diferentes web apps =
diferentes `DashboardSpec` + `MetricSpec`, mismo motor y mismo runtime.

---

## 4. Interactividad: qué hace "dinámico" al tablero

La sensación de "gráfico vivo" no está en el gráfico, sino en que **cada interacción dispara una
consulta rápida y repinta lo que corresponde**. El runtime implementa cinco mecanismos:

| Mecanismo | Qué hace | Cómo se implementa |
|---|---|---|
| **Cross-filtering** | Clic en una marca filtra todo el tablero | El clic emite un filtro al `FilterStore`; todos los paneles releen con el filtro nuevo |
| **Estado en URL** | El tablero es compartible y respeta atrás/adelante | Filtros serializados en el query string (`nuqs`/`URLSearchParams`) |
| **Drill-down** | Bajar de nivel (carrera → paralelo → estudiante-agregado) | Jerarquías declaradas en `ChartSpec.interactions.drilldown` |
| **Slicers y rango temporal** | Controles de filtro explícitos | Componentes de casa que escriben en el mismo `FilterStore` |
| **Refresco / vivo** | Datos frescos sin recargar | Polling por cadencia de la métrica, o SSE para tableros en tiempo real |

**Ciclo de una interacción** (lo que replica a Power BI):

1. El usuario hace clic en la barra "Software".
2. El `FilterStore` agrega `{ carrera: "Software" }` y lo refleja en la URL.
3. Los paneles afectados llaman `useMetric(...)` con el filtro nuevo → `POST /analytics/query`.
4. El motor resuelve desde caché o hace *pushdown* a Postgres (agrega en la BD, **no** trae filas crudas).
5. Devuelve `MetricResult` pequeño → el resolver ya fijó la `ChartSpec` → ECharts repinta.

Todo el trabajo pesado ocurre en el backend; al navegador solo llegan agregados chicos.

---

## 5. Seguridad y privacidad (no negociable)

Los tableros de casa tocan datos de estudiantes, dinero y salud (Core, Kullki, FitBro): PII bajo
**LOPDP**. El módulo hereda el baseline (`yd/`) y añade reglas propias:

- **Solo agregados al cliente.** El motor devuelve conteos y promedios, nunca filas de PII cruda. La
  forma `table` de detalle exige columnas explícitamente no sensibles o pseudonimizadas.
- **Autorización por métrica.** Cada `MetricSpec` declara `roles`; el motor filtra qué métricas y qué
  filas puede ver el usuario (**row-level security**), usando el rol de `yd.auth`. Un docente ve su
  carrera; un coordinador, la suya; admin, todo.
- **Separación de capas (METRICS.md).** Un panel **no mezcla** Uso y Dominio sin etiquetar la clase.
  La telemetría de Uso va pseudonimizada y aislada de las tablas de dominio.
- **Impacto = solo lectura.** Las cifras públicas se leen de la fuente canónica (`/metrics/impact`),
  nunca se recalculan ni se reescriben desde un tablero.
- **Perímetro.** Endpoints detrás de `yd.security` (cabeceras, CORS explícito, rate limit persistente
  en producción). PII enmascarada en logs por `install_pii_masking`.
- **Trazabilidad.** Todo `MetricResult` carga `version` y, si aplica, `modelo@version` (XAI reproducible).

---

## 6. Rendimiento: de dónde sale la "solvencia"

Cuatro trucos, sobre PostgreSQL de casa, dan la respuesta sub-segundo que sentimos en Power BI:

1. **Vistas materializadas / rollups.** Las métricas de alta cadencia se precalculan (el análogo a
   las pre-agregaciones de Power BI / VertiPaq). El `MetricSpec` apunta a la vista, no a la tabla cruda.
2. **Réplica de lectura.** La analítica consulta una réplica, no la BD transaccional: los tableros
   nunca degradan la app.
3. **Query pushdown.** Se agrega en Postgres y se transporta solo el resultado. Jamás filas crudas al front.
4. **Caché por clave.** Redis cachea `(métrica + filtros + versión)`; se invalida por cadencia
   (`on-read` no cachea; `hourly`/`daily` sí). Cambiar la versión de una métrica invalida su caché.

**Escotilla de escape (futuro).** Si una métrica pesada supera lo que Postgres resuelve cómodo, el
motor puede delegar esa métrica a un **DuckDB** embebido (columnar) sin cambiar el contrato. Hoy no
hace falta; queda como punto de extensión declarado.

---

## 7. Estructura de archivos (dónde vive cada cosa)

```
backend/yd/analytics/          # módulo compartido de casa (nuevo)
├── registry.py                # carga y valida MetricSpec (desde DATA_DICTIONARY / YAML)
├── engine.py                  # MetricQuery → SQL → MetricResult
├── resolver.py                # forma → ChartSpec (el "Show Me" de la casa)
├── sql_builder.py             # construcción segura de SQL (parametrizado, sin inyección)
├── cache.py                   # caché Redis por clave versionada
├── security.py                # autorización por métrica + row-level security
└── schemas.py                 # Pydantic: MetricSpec, MetricQuery, MetricResult, ChartSpec

backend/app/routers/analytics.py   # expone el contrato HTTP (consume yd.analytics)

frontend/  →  @yachaydeep/dashboard    # paquete de casa (nuevo)
├── DashboardProvider.tsx      # contexto + FilterStore (Zustand + estado en URL)
├── DashboardRuntime.tsx       # lee DashboardSpec, coloca paneles (react-grid-layout)
├── Panel.tsx                  # un panel: useMetric → ChartRenderer
├── useMetric.ts               # hook de consulta (TanStack Query) al contrato
├── ChartRenderer.tsx          # traduce ChartSpec → opciones de ECharts
├── charts/                    # adaptadores por tipo (bar, line, scatter, heatmap, kpi, table)
└── format binding             # TODO número pasa por frontend/src/lib/format.ts (es-EC)
```

**Contrato HTTP mínimo:**

| Método | Ruta | Devuelve |
|---|---|---|
| `GET` | `/analytics/registry` | Métricas visibles para el rol actual (para armar tableros) |
| `POST` | `/analytics/query` | `{ result: MetricResult, chart: ChartSpec }` para un panel |
| `GET` | `/analytics/dashboard/{id}` | El `DashboardSpec` guardado |
| `POST` | `/analytics/dashboard/query` | Resuelve un tablero completo en un lote (opcional, reduce round-trips) |

Se enciende con el flag **`ENABLE_ANALYTICS`** en `.env`, coherente con el patrón de capacidades
opcionales del starter (piso obligatorio + flags). Un producto sin tableros simplemente no lo activa.

---

## 8. Cómo se monta un tablero nuevo (flujo del desarrollador)

1. **Declarar las métricas** en el `DATA_DICTIONARY` con su clase, forma, fuente y versión. Si es de
   dominio, su SQL vive aquí (regla de casa: nunca en el front).
2. **Crear las vistas** (o materializadas) que esas métricas consumen en Postgres.
3. **Escribir el `DashboardSpec`** (JSON): filtros globales + lista de paneles con su métrica y desglose.
4. **Montar el runtime** en la app: `<DashboardProvider spec={...}><DashboardRuntime/></DashboardProvider>`.
5. **Ajustar overrides** solo si un panel necesita un gráfico distinto al default del resolver.
6. **Verificar marca y formato**: colores desde tokens de casa, números vía `format.ts`, ninguna
   cifra suelta, ningún violeta propio.

No se escribe un solo componente de gráfico por producto. Eso es lo que hace la base **reutilizable
entre web apps distintas**.

---

## 9. Coherencia de marca en los gráficos

Los tableros son superficie de marca; heredan la doctrina (Arquitectura de Marca §7–§8):

- **Color de serie = `--brand-primary`** del producto (Áncora ámbar, Kullki verde, Core dorado…). Para
  varias series, escala derivada del primario + neutros de casa.
- **El dorado es solo acento** (KPIs destacados, barra superior de tarjeta), nunca fondo extenso.
- **El violeta está reservado a terceros.** En una comparativa contra un competidor, ese —y solo ese—
  se pinta violeta. Ningún dato propio usa violeta.
- **Ejes y etiquetas en es-EC** (miles con punto, coma decimal) vía `format.ts`.
- **Estados semánticos:** verde `--ok`, ámbar `--warn`, rojo `--danger` para umbrales (p. ej. riesgo).
- **Tipografía de datos:** `Spline Sans Mono` para cifras y coordenadas; display para títulos de panel.

---

## 10. Fases de implementación

| Fase | Entregable | Formas soportadas |
|---|---|---|
| **1 — Núcleo** | Registry + Engine + Resolver + contrato + runtime con cross-filter y estado en URL | `scalar`, `timeseries`, `category`, `category_wide` |
| **2 — Riqueza** | Drill-down, caché Redis, vistas materializadas, RLS por métrica | `+ part_to_whole`, `timeseries_multi`, `matrix`, `distribution` |
| **3 — Escala** | Escotilla DuckDB, mapas EC (`geo`), bookmarks, refresco vivo (SSE) | `+ geo`, `funnel`, `correlation`, `table` server-side |

Cada fase es desplegable y útil por sí sola. La Fase 1 ya monta tableros interactivos reales.

---

## 11. Gobernanza

- El **registro de métricas se versiona** como el `DATA_DICTIONARY`: cambiar una definición sube su
  `version` y se anota en `CHANGELOG.md`. La caché se invalida por versión.
- Las **formas y el resolver** son parte del módulo de casa: si se añade un tipo de gráfico, se hace
  en `yd-analytics` y se propaga; no se bifurca por producto.
- **Cobertura de tests ≥ 60 %** (regla de casa CI): el motor y el resolver son lógica pura, fáciles
  de testear (dada una forma y una consulta, la `ChartSpec` es determinista).

---

## Anexo · Glosario rápido

- **Forma (`shape`)** — el tipo semántico de una métrica según sus medidas y dimensiones; determina el gráfico.
- **Resolver** — la función determinista forma → `ChartSpec`. El "Show Me" de la casa.
- **Cross-filtering** — que un clic en un panel filtre a todos los demás.
- **Pushdown** — agregar en la base de datos y transportar solo el resultado.
- **Rollup / vista materializada** — precálculo de una métrica para respuesta sub-segundo.
- **RLS (row-level security)** — filtrar filas por el rol del usuario dentro de la misma consulta.

---

*Yachay Deep — Convertimos datos en decisiones. Este módulo convierte esas decisiones en tableros
que cualquier producto de la casa monta sin reinventar la rueda.*
*DASHBOARD.md · Arquitectura de `yd-analytics` v0.1 · Julio 2026.*
