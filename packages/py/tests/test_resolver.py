"""Pruebas del resolver: 'entiende la forma → elige el gráfico'. Sin BD:
se construyen MetricSpec/MetricQuery/MetricResult en memoria."""
from yd_analytics import resolver
from yd_analytics.schemas import MetricQuery, MetricResult, MetricSpec


def _spec(shape, **kw):
    base = dict(id="m", clase="dominio", titulo="m", shape=shape, fuente="t",
                medida={"sql": "COUNT(*)"}, grano=["c"])
    base.update(kw)
    return MetricSpec(**base)


def _result(shape, rows, formato="number"):
    cols = list(rows[0].keys()) if rows else ["valor"]
    return MetricResult(metric="m", shape=shape, unidad="conteo", formato=formato,
                        columns=cols, rows=rows)


def test_scalar_to_kpi():
    sp = _spec("scalar")
    r = _result("scalar", [{"valor": 42}])
    assert resolver.resolve(sp, MetricQuery(metric="m"), r).type == "kpi"


def test_timeseries_to_line_or_area():
    sp = _spec("scalar", dim_temporal="periodo")
    r = _result("timeseries", [{"periodo": "2025-1", "valor": 3}, {"periodo": "2025-2", "valor": 5}])
    c = resolver.resolve(sp, MetricQuery(metric="m", dimensions=["periodo"]), r)
    assert c.type in ("line", "area")


def test_category_low_to_bar_high_to_barh():
    sp = _spec("scalar")
    low = _result("category", [{"c": f"x{i}", "valor": i} for i in range(4)])
    hi = _result("category", [{"c": f"x{i}", "valor": i} for i in range(12)])
    q = MetricQuery(metric="m", dimensions=["c"])
    assert resolver.resolve(sp, q, low).type == "bar"
    assert resolver.resolve(sp, q, hi).type == "bar_h"


def test_part_to_whole_pie_vs_stacked():
    sp = _spec("part_to_whole")
    q = MetricQuery(metric="m", dimensions=["c"])
    few = _result("category", [{"c": "a", "valor": 1}, {"c": "b", "valor": 2}])
    many = _result("category", [{"c": f"x{i}", "valor": i} for i in range(6)])
    assert resolver.resolve(sp, q, few).type == "pie"
    assert resolver.resolve(sp, q, many).type == "stacked_bar"


def test_distribution_correlation_funnel():
    q = MetricQuery(metric="m", dimensions=["c"])
    assert resolver.resolve(_spec("distribution"), q, _result("category", [{"c": "0-10", "valor": 5}])).type == "histogram"
    assert resolver.resolve(_spec("correlation"), q, _result("category", [{"c": 1, "valor": 2}])).type == "scatter"
    assert resolver.resolve(_spec("funnel"), q, _result("category", [{"c": "p1", "valor": 9}])).type == "funnel"


def test_matrix_to_heatmap():
    sp = _spec("scalar")
    r = _result("matrix", [{"a": "x", "b": "y", "valor": 1}])
    c = resolver.resolve(sp, MetricQuery(metric="m", dimensions=["a", "b"]), r)
    assert c.type == "heatmap"


def test_chart_hint_override():
    sp = _spec("scalar")
    r = _result("category", [{"c": "a", "valor": 1}])
    c = resolver.resolve(sp, MetricQuery(metric="m", dimensions=["c"], chart_hint="pie"), r)
    assert c.type == "pie"
