"""
yd_analytics.model — Modelo semántico automático: RELACIONES entre tablas.

Es lo que en Power BI armas a mano (Power Pivot): un modelo con claves foráneas y
relaciones. Aquí se **detecta solo** y permite consultar **cruzando tablas** sin que
el usuario escriba SQL ni DAX — sube o conecta una base, el sistema encuentra cómo se
unen las tablas, y tú preguntas.

Detección (heurística, revisable por humano):
- Columna `X_id` / `X_codigo` en A cuyo tronco apunta a la tabla B (singular/plural)
  con clave `id`/`codigo` → A(X) → B(clave), muchos-a-uno.
- Columna del mismo nombre presente en dos tablas y **única** en una → la única es el
  lado "uno".
"""
from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass, field

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _ident(x: str) -> str:
    if not _IDENT.match(x):
        raise ValueError(f"Identificador inválido: {x!r}")
    return x


def _sing(x: str) -> str:
    x = x.lower()
    if x.endswith("es"):
        return x[:-2]
    return x[:-1] if x.endswith("s") else x


@dataclass
class Relationship:
    from_table: str
    from_col: str
    to_table: str
    to_col: str
    cardinality: str = "many_to_one"
    confidence: float = 0.7


@dataclass
class Model:
    tables: list[str]
    relationships: list[Relationship] = field(default_factory=list)


def _is_unique(conn, table: str, col: str) -> bool:
    n = conn.execute(text(f"SELECT COUNT(*), COUNT(DISTINCT {col}) FROM {table}")).fetchone()
    return n is not None and n[0] == n[1] and n[0] > 0


def detect_relationships(engine: Engine, tables: list[str]) -> list[Relationship]:
    insp = inspect(engine)
    cols = {t: [c["name"] for c in insp.get_columns(t)] for t in tables}
    rels: list[Relationship] = []
    seen: set[tuple] = set()

    with engine.connect() as conn:
        for a in tables:
            for ca in cols[a]:
                low = ca.lower()
                # caso 1: columna *_id / *_codigo → tabla por tronco
                m = re.match(r"^(.*)_(id|codigo|cod)$", low)
                if m:
                    stem = _sing(m.group(1))
                    for b in tables:
                        if b == a:
                            continue
                        if _sing(b) == stem or _sing(b).startswith(stem):
                            key = next((c for c in cols[b] if c.lower() in ("id", "codigo", "cod", m.group(2))), None)
                            if key and _is_unique(conn, b, key):
                                sig = (a, ca, b, key)
                                if sig not in seen:
                                    seen.add(sig)
                                    rels.append(Relationship(a, ca, b, key, "many_to_one", 0.9))
                # caso 2: mismo nombre en A y B, único en uno de los dos
                for b in tables:
                    if b == a or ca not in cols[b]:
                        continue
                    if _is_unique(conn, b, ca) and not _is_unique(conn, a, ca):
                        sig = (a, ca, b, ca)
                        if sig not in seen:
                            seen.add(sig)
                            rels.append(Relationship(a, ca, b, ca, "many_to_one", 0.75))
    return rels


def build_model(engine: Engine, tables: list[str]) -> Model:
    return Model(tables=list(tables), relationships=detect_relationships(engine, tables))


def _path(model: Model, src: str, dst: str) -> list[Relationship] | None:
    """Camino de JOINs entre dos tablas (grafo no dirigido de relaciones)."""
    if src == dst:
        return []
    adj: dict[str, list[Relationship]] = {}
    for r in model.relationships:
        adj.setdefault(r.from_table, []).append(r)
        adj.setdefault(r.to_table, []).append(r)
    q = deque([(src, [])])
    visited = {src}
    while q:
        node, path = q.popleft()
        for r in adj.get(node, []):
            nxt = r.to_table if r.from_table == node else r.from_table
            if nxt in visited:
                continue
            if nxt == dst:
                return path + [r]
            visited.add(nxt)
            q.append((nxt, path + [r]))
    return None


def query_related(engine: Engine, model: Model, *, fact: str, measure: str,
                  dimension: str, dim_table: str | None = None) -> list[dict]:
    """Consulta cruzando tablas: mide `measure` sobre `fact`, desglosado por
    `dim_table.dimension`, resolviendo los JOINs por las relaciones detectadas.
    El usuario nunca escribe el JOIN."""
    dim_table = dim_table or fact
    _ident(fact); _ident(dimension); _ident(dim_table)

    joins = ""
    if dim_table != fact:
        path = _path(model, fact, dim_table)
        if path is None:
            raise ValueError(f"No hay relación entre {fact!r} y {dim_table!r}")
        joined = {fact}
        for r in path:
            # decide qué tabla se incorpora y con qué condición
            if r.from_table in joined and r.to_table not in joined:
                new, on = r.to_table, f"{r.from_table}.{r.from_col} = {r.to_table}.{r.to_col}"
                joined.add(r.to_table)
            elif r.to_table in joined and r.from_table not in joined:
                new, on = r.from_table, f"{r.to_table}.{r.to_col} = {r.from_table}.{r.from_col}"
                joined.add(r.from_table)
            else:
                continue
            joins += f" JOIN {_ident(new)} ON {on}"

    sql = (f"SELECT {dim_table}.{dimension} AS {dimension}, ({measure}) AS valor "
           f"FROM {fact}{joins} GROUP BY {dim_table}.{dimension} ORDER BY valor DESC")
    with engine.connect() as conn:
        res = conn.execute(text(sql))
        cols = list(res.keys())
        return [dict(zip(cols, row)) for row in res.fetchall()]
