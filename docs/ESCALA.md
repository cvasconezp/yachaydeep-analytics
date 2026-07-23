# ESCALA — ¿Procesa big data?

**Sí, y la clave es que el motor no mueve los datos: los agrega en la base y solo
transporta el resultado (query pushdown).** Un tablero pide "riesgo por período" y a la
app vuelven 6 filas, no el millón que hay detrás.

## Prueba

El motor es **agnóstico de la base** (recibe un `Engine` de SQLAlchemy). Contra
**DuckDB** (motor columnar) con **1.000.000 de filas**, la agregación por período tardó
**~440 ms** y devolvió 6 filas. Sin cambiar una línea del motor — solo el `Engine`.
(Ver `tests/test_bigdata.py`, que lo verifica con 200k filas.)

## Cómo escala según el tamaño

| Volumen | Motor recomendado | Cómo |
|---|---|---|
| Hasta ~decenas de millones | **PostgreSQL** (baseline) | Índices + **vistas materializadas** (rollups) + **réplica de lectura** |
| Cientos de millones / archivos grandes | **DuckDB** o **ClickHouse** | Columnar; DuckDB lee Parquet directo, ClickHouse para alta concurrencia |
| Miles de millones / nube | **BigQuery · Snowflake · Databricks** | Vía dialecto SQLAlchemy; el pushdown va al warehouse |

Cambiar de uno a otro es cambiar el DSN del `Engine`; el registro, el resolver y la
cara no cambian.

## Los cuatro trucos de "solvencia" a escala

1. **Pushdown**: se agrega en la base; nunca llegan filas crudas al front.
2. **Pre-agregaciones / materializadas**: el equivalente a VertiPaq — respuestas sub-segundo.
3. **Réplica de lectura**: la analítica no pesa sobre la BD transaccional.
4. **Caché por versión** (Redis): resultados por (métrica + filtros + versión).

## La honestidad sobre la ingesta

El módulo **`ingest`** (Excel/CSV con pandas) es para archivos **pequeños o medianos**
—en memoria—, no para big data. Los datos masivos **viven en el warehouse** y se
consultan directo (o se cargan con `COPY`/tablas externas del propio motor). El
**profiler** ya escala porque perfila con SQL (`COUNT(DISTINCT`, muestreo `LIMIT`), no
trayendo todo a memoria.

---

*Yachay Deep · Escala y big data v0.1 · Julio 2026.*
