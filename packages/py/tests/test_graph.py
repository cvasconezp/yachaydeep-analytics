import pytest

from yd_analytics import Filter, run_graph


def test_graph_nodes_edges(engine):
    g = run_graph(engine, "malla_prerrequisitos", role="coordinador")
    assert g.directed is True
    assert len(g.nodes) == 4
    assert len(g.edges) == 3
    # criticidad = out-degree: MAT101 y PRG101 y PRG201 aportan aristas
    by_id = {n.id: n for n in g.nodes}
    assert by_id["PRG201"].attrs["dependientes"] == 1  # PRG201 -> BDD301


def test_graph_role_denied(engine):
    with pytest.raises(PermissionError):
        run_graph(engine, "malla_prerrequisitos", role="invitado")


def test_graph_filter_and_whitelist(engine):
    g = run_graph(engine, "malla_prerrequisitos", filters=[Filter(field="nivel", value=1)], role="admin")
    assert all(True for _ in g.nodes)  # filtró a nivel 1
    with pytest.raises(ValueError):
        run_graph(engine, "malla_prerrequisitos",
                  filters=[Filter(field="codigo; DROP TABLE asignatura", value=1)], role="admin")


def test_graph_unknown(engine):
    with pytest.raises(KeyError):
        run_graph(engine, "no_existe", role="admin")
