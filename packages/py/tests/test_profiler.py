from yd_analytics import profile


def test_profile_classifies_columns(engine):
    p = profile(engine, "evaluacion_riesgo")
    roles = {c.name: c.role for c in p.columns}
    assert roles["periodo"] == "temporal"
    assert roles["carrera"] == "categorical"
    assert roles["score"] == "numeric"
    assert roles["estudiante_id"] == "id"


def test_profile_proposes_metrics_and_dashboard(engine):
    p = profile(engine, "evaluacion_riesgo")
    ids = {m.id for m in p.metrics}
    assert "evaluacion_riesgo__conteo" in ids
    assert "evaluacion_riesgo__score__promedio" in ids
    # el dashboard propuesto trae un KPI, la serie temporal y paneles por categoría
    panel_metrics = [pn["metric"] for pn in p.dashboard["paneles"]]
    assert "evaluacion_riesgo__conteo" in panel_metrics
    assert any(pn.get("dimensions") == ["periodo"] for pn in p.dashboard["paneles"])
    assert p.dashboard["titulo"].startswith("Tablero automático")


def test_profile_rejects_bad_table(engine):
    import pytest
    with pytest.raises(ValueError):
        profile(engine, "x; DROP TABLE evaluacion_riesgo")
