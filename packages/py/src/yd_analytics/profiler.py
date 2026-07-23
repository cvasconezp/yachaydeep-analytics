"""
yd_analytics.profiler — Auto-perfilado de datos → métricas y tablero propuestos.

Apunta el profiler a una tabla; infiere el tipo semántico de cada columna, propone
métricas candidatas (conteos, distribuciones, promedios, series) y arma un
DashboardSpec inicial. El resolver ya elige el gráfico por forma.

Regla de casa: el profiler SUGIERE; el DATA_DICTIONARY (registro) MANDA. La salida
es un punto de partida para revisión humana, no un registro definitivo.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from .schemas import MetricSpec

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_TEMPORAL = re.compile(r"(fecha|date|periodo|per[ií]odo|anio|a[nñ]o|mes|year|trimestre)", re.I)
_GEO = {"provincia", "canton", "cantón", "parroquia", "distrito", "pais", "país", "ciudad"}
_ID_HINT = re.compile(r"(^id$|_id$|cedula|c[eé]dula|codigo|c[oó]digo|dni|ruc)", re.I)

# tipo semántico → forma que insinúa
SemRole = str  # "temporal"|"categorical"|"categorical_high"|"numeric"|"boolean"|"geo"|"id"|"text"


@dataclass
class ProfiledColumn:
    name: str
    sql_type: str
    distinct: int
    total: int
    role: SemRole
    sample: list[Any] = field(default_factory=list)


@dataclass
class ProfileResult:
    table: str
    total: int
    columns: list[ProfiledColumn]
    metrics: list[MetricSpec]
    dashboard: dict


_ENC_HINT = re.compile(r"(_enc$|_cif|cifrad|encrypted|bidx|blind|_hash$)", re.I)


def _classify(name: str, sql_type: str, distinct: int, total: int) -> SemRole:
    t = sql_type.upper()
    numeric = any(k in t for k in ("INT", "REAL", "FLOAT", "NUMER", "DEC", "DOUBLE"))
    # Columna cifrada / índice ciego: opaca para agregación. Se marca y NO se usa.
    if "BLOB" in t or "BYTEA" in t or _ENC_HINT.search(name):
        return "encrypted"
    if _ID_HINT.search(name) and distinct >= total * 0.9:
        return "id"
    if _TEMPORAL.search(name):
        return "temporal"
    if name.lower() in _GEO:
        return "geo"
    if distinct <= 2:
        return "boolean"
    if numeric and distinct > 15:
        return "numeric"
    if distinct > 25:
        return "categorical_high"
    return "categorical"


def profile(engine: Engine, table: str, *, sample: int = 5) -> ProfileResult:
    if not _IDENT.match(table):
        raise ValueError(f"Nombre de tabla inválido: {table!r}")
    insp = inspect(engine)
    cols = insp.get_columns(table)

    profiled: list[ProfiledColumn] = []
    with engine.connect() as c:
        total = int(c.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar() or 0)
        for col in cols:
            name = col["name"]
            if not _IDENT.match(name):
                continue
            distinct = int(c.execute(text(f"SELECT COUNT(DISTINCT {name}) FROM {table}")).scalar() or 0)
            role = _classify(name, str(col["type"]), distinct, total)
            ex = [r[0] for r in c.execute(text(f"SELECT DISTINCT {name} FROM {table} LIMIT {int(sample)}"))]
            profiled.append(ProfiledColumn(name, str(col["type"]), distinct, total, role, ex))

    # dimensiones disponibles = categóricas + geo + temporal (no ids, no texto libre)
    dims = [c.name for c in profiled if c.role in ("categorical", "categorical_high", "geo")]
    temporal = next((c.name for c in profiled if c.role == "temporal"), None)
    numerics = [c.name for c in profiled if c.role == "numeric"]
    grano = dims + ([temporal] if temporal else [])

    metrics: list[MetricSpec] = []
    # 1) conteo total (escalar / distribuciones)
    metrics.append(MetricSpec(
        id=f"{table}__conteo", clase="dominio", titulo="Conteo de registros",
        descripcion=f"Conteo de filas de {table}.", shape="scalar", unidad="conteo",
        formato="number", fuente=table, medida={"sql": "COUNT(*)"},
        grano=grano, dim_temporal=temporal, version="v1",
    ))
    # 2) promedio por cada numérica
    for col in numerics:
        metrics.append(MetricSpec(
            id=f"{table}__{col}__promedio", clase="dominio", titulo=f"Promedio de {col}",
            descripcion=f"Promedio de {col} en {table}.", shape="scalar", unidad="numero",
            formato="number", fuente=table, medida={"sql": f"AVG({col})"},
            grano=grano, dim_temporal=temporal, version="v1",
        ))

    # 3) DashboardSpec propuesto
    paneles: list[dict] = [{"id": "kpi_total", "metric": f"{table}__conteo", "size": "sm"}]
    if numerics:
        paneles.append({"id": f"kpi_{numerics[0]}", "metric": f"{table}__{numerics[0]}__promedio", "size": "sm"})
    if temporal:
        paneles.append({"id": "serie", "metric": f"{table}__conteo", "dimensions": [temporal],
                        "grain": temporal, "size": "lg"})
    for d in dims[:3]:
        paneles.append({"id": f"por_{d}", "metric": f"{table}__conteo", "dimensions": [d], "size": "md"})

    dashboard = {
        "id": f"{table}-auto", "titulo": f"Tablero automático · {table}",
        "filtrosGlobales": dims[:4], "paneles": paneles,
    }

    return ProfileResult(table=table, total=total, columns=profiled,
                         metrics=metrics, dashboard=dashboard)
