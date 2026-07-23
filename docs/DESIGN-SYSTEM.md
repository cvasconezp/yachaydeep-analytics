# DESIGN-SYSTEM — Sistema de diseño de gráficos

> Los **parámetros visuales** del sistema de analítica de la casa: tokens, paleta
> validada, catálogo de gráficos, estados de componente y accesibilidad. Construido
> con el método de la skill `dataviz` (el color se **computa**, no se estima) y la
> estructura de un design system (tokens → componentes → patrones).

**Versión:** 0.1 · Julio 2026 · Depende de `@yachaydeep/brand` y `packages/dashboard/src/palette.ts`.

---

## 1. Tokens

### 1.1 Color — paleta categórica (validada)

Identidad de serie. **Orden fijo, nunca ciclado.** Sin violeta (reservado a terceros).

| Slot | Tono | Claro | Oscuro |
|---|---|---|---|
| 1 | azul | `#2a78d6` | `#3987e5` |
| 2 | naranja | `#eb6834` | `#d95926` |
| 3 | aqua | `#1baf7a` | `#199e70` |
| 4 | amarillo | `#eda100` | `#c98500` |
| 5 | magenta | `#e87ba4` | `#d55181` |
| 6 | verde | `#008300` | `#008300` |
| 7 | rojo | `#e34948` | `#e66767` |

**Resultado del validador** (`scripts/validate_palette.js`, superficie `#fcfcfb` / `#16181d`):
claro — peor par adyacente CVD ΔE **7,2** (banda 6–8 → obliga encoding secundario:
leyenda + etiquetas directas), normal-vision **19,6**, contraste con *relief* en
aqua/amarillo/magenta; oscuro — **todos PASS**. Para dispersión / mapa (todos-los-pares)
el tope es **3 tonos**; pasado ahí, plegar a «Otros» o facetar.

### 1.2 Color — otros roles

- **Secuencial** (magnitud, heatmaps): un solo tono azul `#cde2fb → #0d366b`.
- **Diverging** (polaridad): azul `#2a78d6` ↔ rojo `#e34948`, gris neutro al centro.
- **Estado** (reservado, con icono + etiqueta): good `#0ca30c`, warning `#fab219`,
  serious `#ec835a`, critical `#d03b3b`. Nunca como «serie 4».
- **Primario de producto** (serie única, KPIs): navy `#1B3A6B` por defecto; se
  sobreescribe por marca (Áncora ámbar, Kullki verde, Core dorado).

### 1.3 Ink y superficie

| Rol | Claro | Oscuro |
|---|---|---|
| Superficie | `#fcfcfb` | `#16181d` |
| Ink primario | `#0b0b0b` | `#ffffff` |
| Ink secundario | `#52514e` | `#c3c2b7` |
| Muted (ejes/labels) | `#898781` | `#898781` |
| Grid (hairline) | `#e1e0d9` | `#2c2c2a` |

**El texto usa tokens de ink, nunca el color de la serie.** El modo oscuro es
**seleccionado** (sus propios pasos), no un volteo automático.

### 1.4 Tipografía, espacio, radio

Sans de la casa (**Instrument Sans**; `system-ui` de respaldo); mono **Spline Sans
Mono** para cifras (con `tabular-nums` en columnas). Radio de tarjeta `14px`.
Cifras es-EC (miles con punto, coma decimal) — un solo formateador.

---

## 2. Catálogo de gráficos (forma → gráfico)

El *resolver* del backend elige por la forma del dato; esta es la correspondencia:

| Trabajo del dato | Forma | Gráfico | Regla |
|---|---|---|---|
| Un titular | scalar | **KPI / stat tile** | delta con icono+color, sparkline opcional |
| Cambio en el tiempo | timeseries | **línea / área** | crosshair; área para volumen |
| Varias series en el tiempo | timeseries_multi | **líneas múltiples** | leyenda; ≤ ~6 series, resto «Otros» |
| Magnitud por categoría | category | **barras (V)** | ≤ 8 categorías |
| Muchas categorías | category_wide | **barras (H) Top-N** | + «Otros» rotulado |
| Parte de un todo | part_to_whole | **dona (≤4) / apiladas 100%** | pie solo ≤ 4 |
| Distribución | distribution | **histograma / boxplot** | — |
| Correlación | correlation | **dispersión** | ≤ 3 grupos (tope all-pairs) |
| Matriz | matrix | **mapa de calor** | rampa secuencial |
| Pasos / conversión | funnel | **embudo** | — |
| Relaciones | graph | **red (NetworkView)** | estilo VOSviewer (cluster/overlay) |
| Detalle | table | **tabla** | también es la «vista tabla» de accesibilidad |

**No-negociables** (skill dataviz): un solo eje por gráfico (nunca doble eje);
color sigue a la entidad, no al ranking; leyenda siempre para ≥ 2 series (ninguna
para una); marcas finas, extremos redondeados 4px; hover por defecto.

---

## 3. Componentes y estados

Cada componente de la cara (`@yachaydeep/dashboard`) define sus estados:

| Componente | Default | Hover | Cargando | Vacío | Error |
|---|---|---|---|---|---|
| **Panel** | gráfico pintado | tooltip por marca | skeleton | «Sin datos para este filtro» | mensaje + reintentar |
| **KPI / tile** | cifra + delta | — | shimmer en la cifra | «—» | «—» con nota |
| **NetworkView** | red con layout de fuerzas | resalta adyacencia | spinner | «Sin relaciones» | mensaje |
| **Slicer / filtro** | valor(es) activo(s) | ghost wash | — | «Todas» | — |

El runtime del tablero maneja `isLoading` / `error` / vacío desde `useMetric`
(TanStack Query) — un panel nunca queda en blanco sin explicación.

---

## 4. Accesibilidad (pase final)

- **Identidad nunca solo por color:** leyenda presente para ≥ 2 series; ≤ 4 series
  además con etiqueta directa. Los tres tonos sub-3:1 en claro (aqua, amarillo,
  magenta) llevan **etiqueta visible o vista de tabla** (regla de *relief*).
- **Vista de tabla** disponible en cada panel (toggle) — datos legibles por lector
  de pantalla y exportables.
- **Modo oscuro seleccionado**, validado contra su propia superficie.
- **Textura** disponible como canal extra para daltonismo / impresión / `forced-colors`.
- **ARIA / teclado:** cada gráfico es `role="img"` con `aria-label`; controles
  (toggles, slicers) son botones enfocables con `aria-pressed`.
- **Contraste de texto:** ink primario/secundario sobre superficie, siempre ≥ 4.5:1.

---

## 5. Dónde vive

- Tokens y paleta: `packages/dashboard/src/palette.ts` (validada con
  `scripts/validate_palette.js`).
- Traductor a ECharts: `packages/dashboard/src/chartOptions.ts`.
- Referencia visual: `examples/standalone-html/gallery-demo.html` (todo el catálogo,
  claro/oscuro).

Un cambio de paleta o de token se hace **aquí y se propaga** — nunca se codifica un
color suelto en un consumidor (misma regla de oro que `@yachaydeep/brand`).

---

*Yachay Deep · Sistema de diseño de gráficos v0.1 · Julio 2026.*
