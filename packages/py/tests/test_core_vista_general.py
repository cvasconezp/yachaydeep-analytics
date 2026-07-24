"""Piloto Vista General: cada métrica de Core da el número correcto.

Se monta una BD SQLite con el esquema de Core y datos conocidos, y se comprueba que el
motor calcule lo mismo que hoy calcula resumen.py. Aísla el SQL de la métrica del
despliegue: prueba que la definición es correcta sin necesitar el Postgres real.
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text

from yd_analytics import MetricQuery, run_query, Filter
from yd_analytics.apps.core import register_all


@pytest.fixture
def engine(tmp_path):
    eng = create_engine(f"sqlite:///{tmp_path/'core.db'}")
    with eng.begin() as c:
        c.execute(text("CREATE TABLE students(id INTEGER, carrera TEXT, periodo TEXT)"))
        c.execute(text("CREATE TABLE enrollments(student_id INTEGER, docente TEXT, asignatura TEXT, carrera TEXT, periodo TEXT)"))
        c.execute(text("CREATE TABLE grades(student_id INTEGER, asignatura TEXT, docente TEXT, carrera TEXT, nota_final REAL, periodo TEXT)"))
        c.execute(text("CREATE TABLE course_configs(codigo_avac TEXT, carrera TEXT)"))

        # 3 estudiantes: 2 en Derecho, 1 en Software
        c.execute(text("INSERT INTO students VALUES (1,'Derecho','P68'),(2,'Derecho','P68'),(3,'Software','P68')"))
        # 4 matrículas, 2 docentes distintos, 3 asignaturas distintas
        c.execute(text("""INSERT INTO enrollments VALUES
            (1,'Ana Perez','Civil','Derecho','P68'),
            (2,'Ana Perez','Penal','Derecho','P68'),
            (3,'Luis Mora','Redes','Software','P68'),
            (1,'Ana Perez','Civil','Derecho','P68')"""))   # est×materia repetida = fila válida
        # notas: promedio (80+60+90)/3 = 76.67; secciones = (Civil,Ana)+(Penal,Ana)+(Redes,Luis)=3
        c.execute(text("""INSERT INTO grades VALUES
            (1,'Civil','Ana Perez','Derecho',80,'P68'),
            (2,'Penal','Ana Perez','Derecho',60,'P68'),
            (3,'Redes','Luis Mora','Software',90,'P68')"""))
        # 2 aulas AVAC
        c.execute(text("INSERT INTO course_configs VALUES ('409001','Derecho'),('409002','Software')"))
    register_all()
    return eng


def _scalar(engine, metric, **kw):
    r = run_query(engine, MetricQuery(metric=metric, **kw))
    return r.result.rows[0]["valor"]


def test_total_estudiantes(engine):
    assert _scalar(engine, "total_estudiantes") == 3


def test_total_docentes(engine):
    assert _scalar(engine, "total_docentes") == 2


def test_total_carreras(engine):
    assert _scalar(engine, "total_carreras") == 2


def test_total_matriculas(engine):
    assert _scalar(engine, "total_matriculas") == 4


def test_promedio_calificaciones(engine):
    assert _scalar(engine, "promedio_calificaciones") == pytest.approx(76.67, abs=0.01)


def test_total_asignaturas(engine):
    assert _scalar(engine, "total_asignaturas") == 3


def test_total_secciones(engine):
    # (Civil,Ana) (Penal,Ana) (Redes,Luis) = 3
    assert _scalar(engine, "total_secciones") == 3


def test_total_aulas_virtuales(engine):
    assert _scalar(engine, "total_aulas_virtuales") == 2


# ── los filtros de la barra (Período, Carrera) ──
def test_filtro_por_carrera(engine):
    r = run_query(engine, MetricQuery(metric="total_estudiantes",
                                      filters=[Filter(field="carrera", value="Derecho")]))
    assert r.result.rows[0]["valor"] == 2, "solo los 2 de Derecho"


def test_filtro_por_periodo(engine):
    r = run_query(engine, MetricQuery(metric="total_matriculas",
                                      filters=[Filter(field="periodo", value="P68")]))
    assert r.result.rows[0]["valor"] == 4


def test_desglose_por_carrera_cross_filter(engine):
    # El bonus: distribución que hoy no está como tarjeta
    r = run_query(engine, MetricQuery(metric="total_estudiantes", dimensions=["carrera"]))
    d = {row["carrera"]: row["valor"] for row in r.result.rows}
    assert d == {"Derecho": 2, "Software": 1}
