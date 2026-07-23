"""#1 Capa de asistencia (reglas + hook LLM) y #4 exportación CSV."""
from yd_analytics import MetricResult, interpret, to_csv


def test_assist_rules_pick_metric_and_dimension():
    s = interpret("¿estudiantes en riesgo por carrera?")
    assert s.query.metric == "estudiantes_en_riesgo"
    assert s.query.dimensions == ["carrera"]
    assert s.confidence > 0


def test_assist_detects_temporal_and_line():
    s = interpret("muéstrame la tendencia del riesgo promedio por periodo")
    assert s.query.metric == "riesgo_promedio"
    assert s.query.dimensions == ["periodo"]
    assert s.chart_hint == "line"


def test_assist_llm_hook():
    def fake_llm(prompt):
        assert "Catálogo" in prompt
        return {"metric": "total_estudiantes", "dimensions": [], "chart_hint": None,
                "rationale": "conteo total"}
    s = interpret("cuántos estudiantes hay", llm=fake_llm)
    assert s.query.metric == "total_estudiantes"
    assert s.confidence == 0.9


def test_export_csv():
    res = MetricResult(metric="m", shape="category", unidad="conteo", formato="number",
                       columns=["carrera", "valor"],
                       rows=[{"carrera": "Software", "valor": 42}, {"carrera": "Educación", "valor": 28}])
    csv = to_csv(res)
    assert csv.splitlines()[0] == "carrera,valor"
    assert "Software,42" in csv
