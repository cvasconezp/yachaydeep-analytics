"""
yd.analytics.graph — Forma de relaciones (shape "graph").

Un grafo de nodos no cabe en el MetricResult tidy: es una red. Aquí el "motor"
corre DOS consultas whitelisted (nodos y aristas) y devuelve un GraphResult.
El render por defecto es un grafo de fuerzas de ECharts (sin dependencia nueva);
vis-network es una alternativa válida en el consumidor.

Seguridad: mismo criterio que el motor tabular — FROM del registro (whitelist),
campos filtrables validados, valores como binds. Autorización por rol.
"""
from __future__ import annotations

import re

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .schemas import Filter, GraphEdge, GraphNode, GraphResult, GraphSpec

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _ident(name: str) -> str:
    if not _IDENT.match(name):
        raise ValueError(f"Identificador inválido: {name!r}")
    return name


# --- Registro de grafos (demo). En prod ← DATA_DICTIONARY / configuración. -- #
_GRAPHS: dict[str, GraphSpec] = {
    "malla_prerrequisitos": GraphSpec(
        id="malla_prerrequisitos",
        titulo="Malla de prerrequisitos",
        descripcion="Nodos = asignaturas; aristas dirigidas = prerrequisito → asignatura.",
        directed=True,
        nodes_from="asignatura", node_id="codigo", node_label="nombre", node_group="nivel",
        edges_from="prerrequisito", edge_source="requiere", edge_target="asignatura",
        filterable=["carrera", "nivel"],
        roles=["docente", "coordinador", "admin"],
        version="v1",
    )
}


def get(graph_id: str) -> GraphSpec:
    if graph_id not in _GRAPHS:
        raise KeyError(f"Grafo no registrado: {graph_id!r}")
    return _GRAPHS[graph_id]


def _where(spec: GraphSpec, filters: list[Filter], params: dict) -> str:
    clauses = []
    for i, f in enumerate(filters):
        if f.field not in spec.filterable:
            raise ValueError(f"Filtro no permitido para {spec.id}: {f.field!r}")
        col = _ident(f.field)
        params[f"g{i}"] = f.value
        clauses.append(f"{col} = :g{i}")
    return (" WHERE " + " AND ".join(clauses)) if clauses else ""


def run_graph(engine: Engine, graph_id: str, *, filters: list[Filter] | None = None,
              role: str = "*") -> GraphResult:
    spec = get(graph_id)
    if role != "*" and "*" not in spec.roles and role not in spec.roles:
        raise PermissionError(f"Rol {role!r} no autorizado para {spec.id}")

    filters = filters or []
    params: dict = {}
    where = _where(spec, filters, params)

    grp = f", {_ident(spec.node_group)} AS grp" if spec.node_group else ", NULL AS grp"
    nodes_sql = (f"SELECT {_ident(spec.node_id)} AS id, {_ident(spec.node_label)} AS label{grp} "
                 f"FROM {_ident(spec.nodes_from)}{where}")

    # Las aristas se limitan a los nodos visibles (respetan el filtro).
    edges_sql = (
        f"SELECT {_ident(spec.edge_source)} AS source, {_ident(spec.edge_target)} AS target "
        f"FROM {_ident(spec.edges_from)} "
        f"WHERE {_ident(spec.edge_source)} IN (SELECT id FROM ({nodes_sql})) "
        f"AND {_ident(spec.edge_target)} IN (SELECT id FROM ({nodes_sql}))"
    )

    with engine.connect() as conn:
        node_rows = [dict(r._mapping) for r in conn.execute(text(nodes_sql), params)]
        edge_rows = [dict(r._mapping) for r in conn.execute(text(edges_sql), params)]

    # value del nodo = out-degree (cuántas asignaturas dependen de él) = criticidad.
    out_deg: dict[str, int] = {}
    for e in edge_rows:
        out_deg[e["source"]] = out_deg.get(e["source"], 0) + 1

    nodes = [
        GraphNode(id=str(n["id"]), label=str(n["label"]),
                  group=None if n["grp"] is None else str(n["grp"]),
                  value=1.0 + out_deg.get(n["id"], 0),
                  attrs={"dependientes": out_deg.get(n["id"], 0)})
        for n in node_rows
    ]
    edges = [GraphEdge(source=str(e["source"]), target=str(e["target"]),
                       kind="prerrequisito") for e in edge_rows]

    return GraphResult(
        graph=spec.id, directed=spec.directed, nodes=nodes, edges=edges,
        meta={"version": spec.version, "clase": spec.clase,
              "n_nodes": len(nodes), "n_edges": len(edges)},
    )
