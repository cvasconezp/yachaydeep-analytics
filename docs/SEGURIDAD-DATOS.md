# SEGURIDAD-DATOS — Analítica sobre datos cifrados

> Cómo `yd-analytics` analiza bases con PII cifrada sin ver las llaves ni el texto
> plano. Complementa el baseline de la casa (`yd/crypto`: Fernet/MultiFernet + blind
> index) y la disciplina de `METRICS.md` (al cliente solo llegan agregados).

## Qué tipo de cifrado (define todo)

| Tipo | Efecto en la analítica |
|---|---|
| **En reposo** (TDE / disco / RDS) | **Transparente.** Postgres descifra al leer; sin cambios. |
| **En tránsito** (TLS) | **Transparente.** Solo `sslmode=require` en el DSN. |
| **A nivel de columna** (`yd/crypto`) | **Opaco.** La columna es un blob; no se puede `SUM/AVG/GROUP/rango`. |

Los dos primeros no requieren nada. El tercero es el que este módulo resuelve.

## Las cuatro piezas (implementadas)

1. **Índice ciego (blind index).** Una `MetricSpec` declara `blind_index = {"cedula":
   "cedula_bidx"}`. Al agrupar por `cedula`, el motor agrupa por el **hash con clave**
   (determinista) y devuelve el hash como etiqueta — nunca el texto plano. Permite
   contar/igualar sin descifrar.
2. **Hook de descifrado de etiquetas.** `run_query(..., decrypt_labels=fn)` donde
   `fn(dim, hashes) -> {hash: texto}` lo provee la app (que sí tiene las llaves, con
   `yd/crypto`). Solo se descifra el **puñado de etiquetas visibles**, no la columna.
   **El paquete nunca recibe las llaves.**
3. **Supresión k-anónima.** `MetricSpec.k_anon = k`: en métricas de conteo, se ocultan
   las celdas con conteo `< k` (evita re-identificar grupos diminutos). El resultado
   reporta cuántas se suprimieron (`meta.k_anon_suprimidas`).
4. **Detección en el profiler.** Columnas `BLOB/BYTEA` o con nombre `*_enc`, `*_cif`,
   `*_bidx`… se clasifican como `encrypted` y **no** se proponen como dimensión ni
   medida; se sugiere su índice ciego o un derivado bucketizado.

## Patrón recomendado (para montos y números)

No se agrega sobre PII: se agrega sobre **dimensiones en claro** (carrera, periodo,
rango de monto). Para números sensibles, un **job de confianza de la app** (con las
llaves) descifra, agrega y escribe **agregados en claro** a una vista de analítica;
`yd-analytics` lee esa vista. Así las llaves y el texto plano nunca salen del
perímetro de la app, y al tablero solo llegan cifras seguras.

```
tablas OLTP cifradas → (job de la app con llaves: descifra + agrega) →
   vistas de analítica (agregados en claro) → yd-analytics → tablero
```

*Yachay Deep · Seguridad de datos en analítica v0.1 · Julio 2026.*
