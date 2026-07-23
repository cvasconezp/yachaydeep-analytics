from sqlalchemy import text

from yd_analytics import profile


def test_profile_flags_encrypted_columns(engine):
    with engine.begin() as c:
        c.execute(text("CREATE TABLE personas(id INTEGER, carrera TEXT, cedula_enc BLOB, nombre_cif TEXT)"))
        c.execute(text("INSERT INTO personas VALUES (1,'Software',X'0a0b','zzz'),(2,'Educación',X'0c0d','yyy')"))
    p = profile(engine, "personas")
    roles = {col.name: col.role for col in p.columns}
    assert roles["cedula_enc"] == "encrypted"    # BLOB → cifrada
    assert roles["nombre_cif"] == "encrypted"    # nombre por patrón _cif
    # las columnas cifradas NO entran como dimensiones del tablero propuesto
    assert "cedula_enc" not in p.dashboard["filtrosGlobales"]


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
