# DISTRIBUCIÓN — El sistema de representación gráfica como paquete de casa

> Cómo `yd-analytics` deja de ser un módulo copiado y pasa a ser **un sistema instalable**
> que Core, Áncora y Kullki **consumen por versión** — igual que `@yachaydeep/brand`, pero para
> datos. Vive *dentro* de cada app (nativo, no embebido), analiza los datos disponibles y genera
> gráficas dinámicas para la toma de decisiones.

**Versión:** 0.1 (borrador) · Julio 2026 · Cayambe, Ecuador
**Depende de:** `DASHBOARD.md` (arquitectura), `docs/DATA_DICTIONARY.md`, baseline `yd/`, `@yachaydeep/brand`

---

## 0. La pregunta y la respuesta corta

> *"¿Algo así como hacemos con el brand? ¿Un repo para analizar datos que otros repos llaman?"*

**Sí, es posible y es exactamente el camino correcto.** El brand ya te enseñó el patrón: una fuente
única, versionada, que todos importan y nadie bifurca. La analítica sigue el mismo principio, con **un
matiz**: el brand son *tokens estáticos* (colores, fuentes); la analítica es *lógica viva* que necesita
**leer datos** (backend) y **pintarlos** (frontend). Por eso no es un paquete, son **tres artefactos
versionados juntos** en un repo de casa. Nada se embebe: cada app monta los componentes en sus propias
rutas, con su sesión y su marca.

---

## 1. El modelo "como el brand" — y en qué se diferencia

| | `@yachaydeep/brand` | `yachaydeep-analytics` (nuevo) |
|---|---|---|
| Qué distribuye | Tokens estáticos (color, tipografía, logos) | Un sistema de análisis + representación de datos |
| Naturaleza | Datos inertes (`theme.css`, `tokens.json`) | Lógica: leer datos, interpretarlos, graficarlos |
| Artefactos | **1** paquete | **3** artefactos que se versionan juntos |
| Consumo | `npm i @yachaydeep/brand` | 1 paquete Python + 1 paquete npm + 1 contrato |
| Regla de oro | Un cambio se hace en el paquete y se propaga | Idéntica |

Los **tres artefactos** del repo de analítica:

1. **`@yachaydeep/analytics-contract`** — el contrato: los tipos y JSON Schema de `MetricSpec`,
   `MetricQuery`, `MetricResult`, `ChartSpec`, `GraphResult`. Es la **fuente de verdad** que ambas caras
   importan; publicado como paquete npm (tipos TS) y como JSON Schema (para validar en Python). Que las
   dos caras dependan de él es lo que **evita que se desincronicen**.
2. **`yd-analytics`** (Python) — el **cerebro**: `registry`, `engine`, `sql_builder`, `resolver`,
   `graph`, `cache`, `security` y el `profiler` (§3). Se instala en el backend de cada app y expone un
   `APIRouter` que la app monta bajo `/analytics`.
3. **`@yachaydeep/dashboard`** (npm/React) — la **cara**: `DashboardProvider`, `Panel`, `ChartRenderer`
   (ECharts), `NetworkView` (grafos, con el tema estilo VOSviewer §5), `filterStore`, `useMetric`. Se
   instala en el frontend de cada app.

> Regla mental: **brand = tokens; analytics = contrato + cerebro + cara.** El contrato es el pegamento.

---

## 2. "Vive dentro, no embebido" — la diferencia clave

Esto es lo que separa tu visión de "meter un Power BI en un iframe".

**Embebido** (iframe / Power BI Embedded / Tableau embed): una aplicación *ajena* dentro de un marco,
con su propia sesión, su propio look, su propio dominio. El usuario "entra" a otra cosa. Poco control,
doble login, marca inconsistente.

**Nativo** (lo que hacemos): la app **importa componentes** y los monta en **sus** rutas
(`/tablero`, `/analitica`), con **su** auth (`yd.auth`), **sus** tokens de marca (Áncora ámbar, Kullki
verde) y consultando **sus** endpoints `/analytics` — servidos por el paquete Python *dentro del propio
FastAPI de la app*. El usuario nunca sale de la aplicación. Cero iframes.

```
   App Áncora (repo propio)                      App Kullki (repo propio)
   ┌───────────────────────────┐                ┌───────────────────────────┐
   │ frontend (React)          │                │ frontend (React)          │
   │  import @yachaydeep/       │                │  import @yachaydeep/       │
   │    dashboard  ─┐          │                │    dashboard  ─┐          │
   │  <Dashboard spec={…}/>    │                │  <Dashboard spec={…}/>    │
   │  tokens: ámbar            │                │  tokens: verde            │
   │ backend (FastAPI)         │                │ backend (FastAPI)         │
   │  import yd_analytics ─┐   │                │  import yd_analytics ─┐   │
   │  app.include_router(…) │  │                │  app.include_router(…) │  │
   │  /analytics/* ← su BD  │  │                │  /analytics/* ← su BD  │  │
   └────────┬──────────────┘  │                └────────┬──────────────┘  │
            │  dependen de (por versión)                 │
            ▼                                             ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │           repo  yachaydeep-analytics  (fuente única)                   │
   │   @yachaydeep/analytics-contract · yd-analytics (py) · @yd/dashboard   │
   └──────────────────────────────────────────────────────────────────────┘
```

Mismos componentes, distinto tema y distintos datos: **el mismo dashboard se ve ámbar en Áncora y verde
en Kullki**, sin tocar el paquete — exactamente como el brand ya hace con el color.

---

## 3. "Que analice los datos disponibles y genere gráficas" — el auto-profiler

Para que el sistema sea **completo** (que no haya que declarar todo a mano) se añade una pieza nueva al
cerebro: el **profiler**. Dado un dataset o una tabla, infiere el tipo semántico de cada campo y
**propone** métricas y un tablero inicial. Es el "arrastra tus datos y obtén gráficas", con revisión
humana.

**Qué hace, paso a paso:**

1. **Perfila el esquema + una muestra:** clasifica cada columna → temporal, categórica de baja
   cardinalidad, categórica de alta cardinalidad, numérica continua, booleana, geográfica (cantón/
   provincia EC), identificador, o texto libre.
2. **Propone métricas candidatas:** conteos y distribuciones por cada categórica; series por cada
   temporal; promedios/sumas por cada numérica; correlaciones entre numéricas; relaciones (grafo) si
   detecta pares de claves que se referencian.
3. **Arma un `DashboardSpec` inicial:** elige paneles y, vía el **resolver**, el gráfico de cada uno
   por su forma (KPI, línea, barras, dona, heatmap, red).
4. **Entrega para revisión:** el equipo del producto afina definiciones, nombres y permisos, y las
   asciende al `DATA_DICTIONARY` (que es el registro definitivo). El profiler *sugiere*; el diccionario
   *manda*.

Así, incorporar analítica a un producto nuevo es: apuntar el profiler a sus datos → revisar el tablero
propuesto → publicar. No se parte de una hoja en blanco.

---

## 4. Cómo consume cada app (Core, Áncora, Kullki)

Seis pasos, una sola vez por producto:

1. **Instalar por versión** los tres artefactos: `pip install yd-analytics==X.Y.Z` (backend) y
   `npm i @yachaydeep/dashboard@X.Y.Z @yachaydeep/analytics-contract@X.Y.Z` (frontend).
2. **Montar el router** en su FastAPI: `app.include_router(yd_analytics.router)` → aparece `/analytics/*`.
3. **Conectar su BD y su rol:** el engine lee la BD del producto (réplica de lectura) y el rol sale de
   `yd.auth`. Autorización por métrica incluida.
4. **Declarar su registro** desde su `DATA_DICTIONARY` — o correr el **profiler** para generarlo.
5. **Definir sus `DashboardSpec`** (JSON): qué paneles y filtros.
6. **Montar la cara** en sus rutas: `<Dashboard spec={…} />`, aplicando **sus** tokens de marca. Cada
   número pasa por el formateador es-EC de la casa.

Ningún producto escribe un componente de gráfico. Eso es lo que lo hace **reutilizable entre apps**.

---

## 5. El estilo VOSviewer es un *tema*, no otra herramienta

El mapa que enviaste (overlay de países coloreado por año, escala continua, nodos por peso, aristas
curvas) es la forma **`graph`** con un **tema de overlay**. No hace falta VOSviewer ni otra librería:
ECharts (`graph` + `visualMap` continuo) da ese look. La receta del estilo:

- **Nodos** sin borde, **tamaño por peso** (grado/centralidad), **etiqueta centrada** cuyo tamaño
  escala con el peso.
- **Aristas** curvas y translúcidas (`curveness`, baja opacidad) para leer la maraña de vínculos.
- **Color continuo (overlay)** por un atributo numérico —año, score, tasa de aprobación, mora— con una
  escala tipo *viridis* (morado→verde→amarillo) y **leyenda de gradiente**. Esto es lo distintivo de
  VOSviewer frente a un grafo coloreado por categoría.
- **Modo densidad** opcional (heat) y lienzo blanco, sin ejes.

En la casa: **Research** (co-citación/colaboración, overlay por año), **Áncora** (malla de
prerrequisitos, overlay por tasa de aprobación → ves qué asignaturas "críticas" además reprueban),
**Kullki** (red de préstamos, overlay por mora, grosor por monto). Es el mismo `NetworkView` con
`theme: "overlay"` y un campo numérico para el color. *(Ver el demo `vosviewer-demo.html`.)*

---

## 6. Gobernanza y versionado (como el brand §12)

- **Repo único `yachaydeep-analytics`** (monorepo con los tres artefactos) = fuente de verdad. **SemVer.**
- **El contrato manda.** Un cambio se hace en el paquete y se propaga: `npm update` / `pip install -U`.
  Un cambio incompatible del contrato es *major*, con período de compatibilidad anunciado.
- **Métricas y formas viven en el paquete**, nunca se bifurcan por producto (igual que "un cambio de
  color se hace en `@yachaydeep/brand`, no en el consumidor").
- **Métricas versionadas** (el `registry` ya lo hace): cambiar una definición sube su versión e
  invalida su caché.
- **CI** publica los paquetes al aprobar; los consumidores fijan versión y actualizan cuando deciden.

---

## 7. Estructura propuesta del monorepo

```
yachaydeep-analytics/
├── packages/
│   ├── contract/            @yachaydeep/analytics-contract  (tipos TS + JSON Schema)
│   ├── py/                  yd-analytics  (registry, engine, resolver, graph, profiler, security)
│   └── dashboard/           @yachaydeep/dashboard  (Provider, Panel, ChartRenderer, NetworkView)
├── examples/                apps mínimas de demostración (las que ya tienes de referencia)
├── docs/                    DASHBOARD.md · DISTRIBUCION.md · DATA_DICTIONARY (plantilla)
└── .github/workflows/       CI: tests + publicación de los 3 artefactos por versión
```

---

## 8. Hoja de ruta de adopción

| Fase | Qué | Resultado |
|---|---|---|
| **0 · Extraer** | Mover el módulo de referencia a `yachaydeep-analytics` (3 artefactos) y publicar el contrato | El sistema deja de copiarse; se instala |
| **1 · Core** | Primer consumidor (mayor volumen): profiler + tableros de alerta temprana | Prueba de valor con datos reales |
| **2 · Áncora + Kullki** | Áncora: grafo de prerrequisitos estilo overlay; Kullki: red de préstamos por mora | La red como herramienta de decisión, con marca propia |
| **3 · Avanzado** | Overlay/densidad, mapas de Ecuador (`geo`), tiempo real (SSE), pre-agregaciones | Paridad de "solvencia" con Power BI a escala |

Cada fase es desplegable por sí sola; la Fase 0 es la que convierte esto en "sistema de casa".

---

## 9. Resumen en una frase

Sí: creamos **un repo de analítica** como el del brand, pero con **tres piezas versionadas** (contrato +
cerebro Python + cara React) que cada app **instala y monta en sus propias rutas** — nativo, con su
marca y su sesión. Un **profiler** lee los datos disponibles y propone las gráficas; el **resolver** las
elige por forma; y el estilo **VOSviewer** es solo un tema del renderizador de redes. Todo se decide una
vez, en el paquete, y se propaga a Core, Áncora y Kullki por versión.

---

*Yachay Deep · un producto de Yachay Deep · `yachaydeep-analytics` (distribución) v0.1 · Julio 2026*
