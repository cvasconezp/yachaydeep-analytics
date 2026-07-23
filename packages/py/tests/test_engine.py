import pytest

from yd_analytics import Filter, MetricQuery, run_query


def test_scalar_kpi(engine):
    r = run_query(engine, MetricQuery(metric="estudiantes_en_riesgo", params={"umbral": 0.5}),
                  role="coordinador")
    assert r.result.shape == "scalar"
    assert r.chart.type == "kpi"
    assert r.result.rows[0]["valor"] >= 0


def test_category_bar_and_cross_filter(engine):
    r = run_query(engine, MetricQuery(metric="estudiantes_en_riesgo", dimensions=["carrera"],
                                      params={"umbral": 0.4}), role="docente")
    assert r.result.shape == "category"
    assert r.chart.type in ("bar", "bar_h")
    assert r.chart.interactions.emits_filter == "carrera"


def test_timeseries(engine):
    r = run_query(engine, MetricQuery(metric="riesgo_promedio", dimensions=["periodo"]))
    assert r.result.shape == "timeseries"
    assert r.chart.type in ("line", "area")
    assert len(r.result.rows) == 3


def test_role_denied(engine):
    with pytest.raises(PermissionError):
        run_query(engine, MetricQuery(metric="estudiantes_en_riesgo"), role="invitado")


def test_injection_blocked(engine):
    with pytest.raises(ValueError):
        run_query(engine, MetricQuery(metric="riesgo_promedio",
                                      dimensions=["score; DROP TABLE evaluacion_riesgo"]))
