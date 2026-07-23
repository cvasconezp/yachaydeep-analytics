"""
yd.analytics.sql_builder — Construcción SEGURA de SQL.

Reglas de seguridad:
- El FROM sale del spec (whitelist), nunca del cliente.
- Las dimensiones y los campos de filtro se validan contra spec.grano (whitelist);
  un campo no declarado se rechaza. Así el cliente nunca inyecta identificadores.
- Los valores van SIEMPRE como parámetros ligados (nunca interpolados).
- La expresión de medida es del registro de casa (confiable), no del cliente.
"""
from __future__ import annotations

import re

from .schemas import Filter, MetricQuery, MetricSpec

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _check_ident(name: str) -> str:
    if not _IDENT.match(name):
        raise ValueError(f"Identificador inválido: {name!r}")
    return name


def _allowed(spec: MetricSpec) -> set[str]:
    fields = set(spec.grano)
    if spec.dim_temporal:
        fields.add(spec.dim_temporal)
    return fields


def build(spec: MetricSpec, query: MetricQuery) -> tuple[str, dict]:
    """Devuelve (sql, params). params ya filtrado a los binds usados."""
    allowed = _allowed(spec)
    params: dict = {}

    # 1) Dimensiones de desglose (whitelist).
    #    Si una dimensión está cifrada, se agrupa por su ÍNDICE CIEGO (blind index):
    #    permite contar/igualar sin exponer el texto plano. La etiqueta será el hash;
    #    el motor puede traducirla con el hook decrypt_labels.
    dims = []          # nombres de salida (alias)
    group_exprs = []   # columnas reales por las que se agrupa
    for d in query.dimensions:
        if d not in allowed:
            raise ValueError(f"Dimensión no permitida para {spec.id}: {d!r}")
        alias = _check_ident(d)
        real = _check_ident(spec.blind_index.get(d, d))   # blind index si aplica
        dims.append(alias)
        group_exprs.append(real)

    # 2) SELECT: dimensiones (alias) + medida (alias 'valor').
    select_cols = [f"{g} AS {a}" if g != a else a for a, g in zip(dims, group_exprs)]
    select_cols.append(f"({spec.medida.sql}) AS valor")
    sql = f"SELECT {', '.join(select_cols)} FROM {_check_ident(spec.fuente)}"

    # 3) WHERE desde filtros (parametrizado).
    where = []
    for i, f in enumerate(query.filters):
        if f.field not in allowed:
            raise ValueError(f"Filtro no permitido para {spec.id}: {f.field!r}")
        col = _check_ident(f.field)
        where.append(_render_filter(col, f, i, params))
    if where:
        sql += " WHERE " + " AND ".join(where)

    # 4) GROUP BY / ORDER BY (se agrupa por la columna real, cifrada o no).
    if dims:
        sql += " GROUP BY " + ", ".join(group_exprs)
        # temporal → orden cronológico; categórica → por valor desc.
        if len(dims) == 1 and dims[0] == spec.dim_temporal:
            sql += f" ORDER BY {group_exprs[0]} ASC"
        else:
            sql += " ORDER BY valor DESC"

    # 5) LIMIT (para Top-N; el motor detecta truncamiento aparte).
    if query.limit and dims:
        sql += f" LIMIT {int(query.limit)}"

    # 6) Parámetros de medida (p. ej. :umbral): los de la consulta y, si faltan,
    #    los valores por defecto declarados en la métrica.
    merged = {**spec.param_defaults, **query.params}
    for k, v in merged.items():
        if f":{k}" in sql:
            params[k] = v

    return sql, params


def _render_filter(col: str, f: Filter, i: int, params: dict) -> str:
    if f.op == "eq":
        params[f"f{i}"] = f.value
        return f"{col} = :f{i}"
    if f.op == "gte":
        params[f"f{i}"] = f.value
        return f"{col} >= :f{i}"
    if f.op == "lte":
        params[f"f{i}"] = f.value
        return f"{col} <= :f{i}"
    if f.op == "between":
        lo, hi = f.value
        params[f"f{i}_lo"], params[f"f{i}_hi"] = lo, hi
        return f"{col} BETWEEN :f{i}_lo AND :f{i}_hi"
    if f.op == "in":
        vals = list(f.value)
        keys = []
        for j, v in enumerate(vals):
            params[f"f{i}_{j}"] = v
            keys.append(f":f{i}_{j}")
        return f"{col} IN ({', '.join(keys)})" if keys else "1=0"
    raise ValueError(f"Operador no soportado: {f.op!r}")
