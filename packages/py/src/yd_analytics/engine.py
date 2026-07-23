"""
yd.analytics.engine — Motor de métricas.

Resuelve una MetricQuery contra la base (PostgreSQL en producción; SQLite en el
demo) y devuelve un MetricResult normalizado en formato largo/tidy, con la forma
EFECTIVA ya resuelta según las dimensiones pedidas.

Regla de casa: TODA métrica de dominio se calcula aquí, nunca en el frontend.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine

from . import registry, sql_builder
from .cache import cache
from .schemas import MetricQuery, MetricResult, Shape, Truncation


def _effective_shape(spec, query: MetricQuery) -> Shape:
    """Forma efectiva según cuántas y qué dimensiones pidió el panel (§2.2)."""
    dims = query.dimensions
    if not dims:
        return "scalar"
    if len(dims) == 1:
        if dims[0] == spec.dim_temporal:
            return "timeseries"
        return "category"          # category vs category_wide lo afina el resolver
    if len(dims) == 2:
        if spec.dim_temporal in dims:
            return "timeseries_multi"
        return "matrix"
    return "table"


def run(engine: Engine, query: MetricQuery, *, role: str = "*",
        decrypt_labels=None) -> MetricResult:
    spec = registry.get(query.metric)

    # Autorización por métrica (§5). role='*' = contexto interno/superusuario (bypass).
    if role != "*" and "*" not in spec.roles and role not in spec.roles:
        raise PermissionError(f"Rol {role!r} no autorizado para {spec.id}")

    shape = _effective_shape(spec, query)
    sql, params = sql_builder.build(spec, query)

    # Caché por clave versionada (no cachea 'on-read').
    key = cache.key(spec, query)
    cached = None if spec.cadencia == "on-read" else cache.get(key)
    if cached is not None:
        rows = cached
        was_cached = True
    else:
        with engine.connect() as conn:
            res = conn.execute(text(sql), params)
            cols = list(res.keys())
            rows = [dict(zip(cols, r)) for r in res.fetchall()]
        # normaliza el escalar: valor plano en vez de fila
        if spec.cadencia != "on-read":
            cache.set(key, rows, ttl=cache.ttl_for(spec.cadencia))
        was_cached = False

    columns = ([*query.dimensions, "valor"]) if query.dimensions else ["valor"]
    out_rows = rows if query.dimensions else _scalar_rows(rows)

    # Privacidad: supresión k-anónima (LOPDP). Solo métricas de conteo con desglose.
    suppressed = 0
    if spec.k_anon > 0 and query.dimensions and spec.unidad == "conteo":
        kept = [r for r in out_rows if (r.get("valor") or 0) >= spec.k_anon]
        suppressed = len(out_rows) - len(kept)
        out_rows = kept

    # Privacidad: traducir etiquetas de índice ciego (hash → texto) vía hook de la app.
    if decrypt_labels and query.dimensions:
        for d in query.dimensions:
            if d in spec.blind_index:
                mapping = decrypt_labels(d, [r[d] for r in out_rows])
                for r in out_rows:
                    r[d] = mapping.get(r[d], r[d])

    # Truncamiento honesto (§2.1): si pusimos LIMIT, reportamos cuántos había.
    truncated = None
    if query.limit and query.dimensions:
        total = _count_groups(engine, query)
        if total > len(rows):
            truncated = Truncation(shown=len(out_rows), total=total)

    return MetricResult(
        metric=spec.id,
        shape=shape,
        unidad=spec.unidad,
        formato=spec.formato,
        columns=columns,
        rows=out_rows,
        meta={
            "version": spec.version,
            "modelo": f"{spec.modelo['nombre']}@{spec.modelo['version']}" if spec.modelo else None,
            "clase": spec.clase,
            "cached": was_cached,
            "k_anon_suprimidas": suppressed,
            "sql": sql,   # útil en el demo; en producción se omite o va detrás de flag debug
        },
        truncated=truncated,
    )


def _scalar_rows(rows: list[dict]) -> list[dict]:
    val = rows[0]["valor"] if rows else 0
    return [{"valor": val}]


def _count_groups(engine: Engine, query: MetricQuery) -> int:
    """Cuenta cuántos grupos hay realmente (para el aviso de Top-N)."""
    spec = registry.get(query.metric)
    inner = MetricQuery(
        metric=query.metric, dimensions=query.dimensions,
        filters=query.filters, params=query.params,
    )
    sql, params = sql_builder.build(spec, inner)
    with engine.connect() as conn:
        n = conn.execute(text(f"SELECT COUNT(*) FROM ({sql})"), params).scalar()
    return int(n or 0)
