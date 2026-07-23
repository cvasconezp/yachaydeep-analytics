# VS-POWERBI — Cómo igualar (y superar) a Power BI

> Mapa honesto de qué hace Power BI, qué hace hoy `yachaydeep-analytics`, y el camino
> para igualarlo donde falta y superarlo donde importa. La tesis: **no ganamos siendo
> un Power BI más; ganamos siendo lo que Power BI no puede ser — nativo, a medida y de
> marca dentro de tus productos, y accesible sin DAX.**

## 1. Posicionamiento

Power BI es una **herramienta externa** que el usuario abre (o embebes en un iframe),
con su login, su look y su modelo de licencias por asiento. Yachay Deep Analytics es un
**sistema que vive dentro de tu app** (Core, Áncora, Kullki): misma sesión, misma marca,
mismas rutas. Esa diferencia es la ventaja estratégica; el resto es cerrar brechas de
funcionalidad.

## 2. Feature por feature

| Capacidad de Power BI | En yachaydeep-analytics | Estado |
|---|---|---|
| Catálogo de visuales | KPI, línea/área, barras, apiladas, dona, treemap, dispersión, histograma, boxplot, heatmap, embudo, **red (VOSviewer)**, **coroplético EC** | ✅ a la par |
| "Show Me" (elige el gráfico) | **resolver** por forma del dato (determinista, auditable) | ✅ a la par |
| Cross-highlighting | Sí (resaltado parcial en cada visual) | ✅ a la par |
| Slicers / filtros / drill | Sí (estado en URL, cross-filter, drill declarado) | ✅ a la par |
| Modelo de datos + relaciones (Power Pivot) | **Detección automática de relaciones** (`model`) + consulta cruzando tablas | 🟢 a la par, **sin armarlo a mano** |
| DAX (medidas) | Medidas en el registro/`DATA_DICTIONARY` (SQL) + `param_defaults` | 🟢 equivalente, más simple |
| Q&A (preguntar en lenguaje natural) | **`interpret`** (reglas + LLM: Cerebras/Kimi) | 🟢 a la par, y **tuyo** |
| Power Query (limpieza/ETL) | **`ingest`** (Excel/CSV → limpieza + normalización es-EC) + `yd/etl` | 🟢 a la par en lo esencial |
| Perfilado automático | **`profile`** propone métricas + tablero | 🟢 lo hace solo |
| Tema / branding | Tokens por producto (paleta **validada** para daltonismo) | 🟢 superior (a medida) |
| Exportar (PNG/CSV) | `exportPNG` / `to_csv` | ✅ a la par |
| Seguridad de datos / PII | Índice ciego, k-anonimato, sin llaves en la capa de analítica | 🟢 superior para PII/LOPDP |
| **Modelado visual drag-and-drop** para no técnicos | — | 🔴 brecha |
| **Marketplace de conectores** (cientos) | Conectores por adaptador SQLAlchemy (Postgres foco) | 🔴 brecha de amplitud |
| **Gateways / refresh empresarial** administrados | Réplicas + cadencia/caché propias | 🟡 parcial |
| Ecosistema/comunidad, certificaciones | — | 🔴 brecha |

## 3. La respuesta al "sin DAX ni Power Pivot"

Tu idea central —que alguien **suba o conecte una base y solo pregunte**— es justo donde
cerramos la brecha más difícil de Power BI:

1. **`ingest`** limpia y normaliza el Excel/CSV y lo carga.
2. **`model.detect_relationships`** descubre solo cómo se unen las tablas (claves
   foráneas por nombre y por unicidad) — el *modelo* que en Power BI armas arrastrando.
3. **`query_related`** consulta **cruzando tablas** armando los JOIN por ti — nadie
   escribe SQL ni DAX.
4. **`interpret`** (con tu Cerebras) traduce la pregunta en lenguaje natural a esa
   consulta; el **resolver** elige el gráfico.

Resultado: subir datos → el sistema entiende su forma y sus relaciones → preguntar en
español → tablero. Sin fórmulas.

## 4. Dónde ya somos superiores

- **Nativo, no embebido:** vive dentro de la app, con su sesión y su marca. Cero iframes.
- **A medida y de marca:** el mismo tablero se ve ámbar en Áncora y verde en Kullki.
- **Accesibilidad por construcción:** paleta validada (CVD-safe, claro/oscuro), no por gusto.
- **IA de entendimiento tuya:** el modelo (Cerebras/Kimi) es tuyo, no una caja negra ajena.
- **Privacidad:** analítica sobre datos cifrados sin exponer llaves ni PII (LOPDP).
- **Costo y control:** software de la casa, sin licencia por asiento; los datos no salen.

## 5. Hoja de ruta para cerrar las brechas

| Prioridad | Brecha | Camino |
|---|---|---|
| Alta | Modelado visual para no técnicos | UI de "modelo": ver relaciones detectadas, confirmarlas/editarlas, marcar hechos y dimensiones (arrastrar) |
| Alta | Constructor de tablero sin código | Editor visual sobre el `DashboardSpec` (agregar panel, elegir métrica y desglose) |
| Media | Amplitud de conectores | Adaptadores por fuente (MySQL, SQL Server, Sheets, APIs) sobre SQLAlchemy + un catálogo |
| Media | Refresh/programación | Materializadas + cadencia + un scheduler de refresco |
| Baja | Métricas avanzadas tipo DAX | Un mini-DSL de medidas por encima del registro (ventanas, time-intelligence) |

## 6. Recomendación

Para tableros **dentro de** Core/Áncora/Kullki, reemplazar Power BI tiene todo el
sentido: ya estamos a la par en lo visual e interactivo, y por delante en integración,
marca, IA y privacidad. Donde Power BI aún gana es en que **analistas ajenos** construyan
reportes solos sin tocar código — y esa es exactamente la brecha que cierran los dos
primeros ítems de la hoja de ruta (modelo visual + constructor de tablero). Cerrados
esos, no hay razón para pagar Power BI en la casa.

---

*Yachay Deep · Analytics vs. Power BI v0.1 · Julio 2026.*
