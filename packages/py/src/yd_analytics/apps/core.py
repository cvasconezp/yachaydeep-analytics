"""Métricas de Yachay Deep Core para el motor de analytics.

Piloto: la pestaña "Vista General" del Análisis Institucional. Cada tarjeta que hoy
calcula backend/routes/analytics/resumen.py se declara aquí como una MetricSpec, con el
MISMO SQL, para que el número salga idéntico.

RESTRICCIONES DEL MOTOR (verificadas en sql_builder.py) que condicionan estas métricas:
  - El FROM es UNA sola tabla (`fuente`); no hay JOINs. Cada filtro/dimensión debe ser
    una columna de esa tabla y estar en `grano`.
  - La medida usa columnas SIN prefijo de tabla (el FROM ya fija la tabla).
  - Se evita sintaxis solo-Postgres para que corra igual en SQLite (tests) y Postgres
    (producción): p. ej. secciones usa `a || '|' || b`, no `(a, b)`.

CAVEAT #1 A VERIFICAR CONTRA DATOS REALES (no es un bug de aquí, es del dato):
  `students.periodo` guarda formato "2026-1"; `grades`/`enrollments` usan "P68"/"68".
  Filtrar `total_estudiantes` por periodo="P68" podría devolver 0. Core lo resuelve con
  normalización en resumen.py. Para el piloto: comparar SIN filtro de período primero, y
  si al filtrar no cuadra, es ESTO — no un dato perdido.
"""
from ..schemas import MetricSpec, Measure
from .. import registry

# Tablas reales de Core
CORE_VISTA_GENERAL = [
    MetricSpec(
        id="total_estudiantes", clase="uso", titulo="Estudiantes",
        descripcion="Estudiantes distintos.", shape="scalar", unidad="conteo",
        formato="number", fuente="students",
        medida=Measure(sql="COUNT(DISTINCT id)"),
        grano=["periodo", "carrera"], dim_temporal="periodo", version="v1",
    ),
    MetricSpec(
        id="total_docentes", clase="uso", titulo="Docentes",
        descripcion="Docentes distintos en matrículas.", shape="scalar", unidad="conteo",
        formato="number", fuente="enrollments",
        medida=Measure(sql="COUNT(DISTINCT docente)"),
        grano=["periodo", "carrera"], dim_temporal="periodo", version="v1",
    ),
    MetricSpec(
        id="total_carreras", clase="uso", titulo="Carreras",
        descripcion="Carreras con al menos un estudiante.", shape="scalar", unidad="conteo",
        formato="number", fuente="students",
        medida=Measure(sql="COUNT(DISTINCT carrera)"),
        grano=["periodo"], dim_temporal="periodo", version="v1",
    ),
    MetricSpec(
        id="total_matriculas", clase="uso", titulo="Matrículas",
        descripcion="Registros estudiante × materia.", shape="scalar", unidad="conteo",
        formato="number", fuente="enrollments",
        medida=Measure(sql="COUNT(*)"),
        grano=["periodo", "carrera"], dim_temporal="periodo", version="v1",
    ),
    MetricSpec(
        id="promedio_calificaciones", clase="uso", titulo="Prom. calificaciones",
        descripcion="Promedio de notas finales.", shape="scalar", unidad="puntos",
        formato="number", fuente="grades",
        medida=Measure(sql="ROUND(CAST(AVG(nota_final) AS numeric), 2)"),
        grano=["periodo", "carrera"], dim_temporal="periodo", version="v1",
    ),
    MetricSpec(
        id="total_asignaturas", clase="uso", titulo="Asignaturas",
        descripcion="Materias únicas.", shape="scalar", unidad="conteo",
        formato="number", fuente="enrollments",
        medida=Measure(sql="COUNT(DISTINCT asignatura)"),
        grano=["periodo", "carrera"], dim_temporal="periodo", version="v1",
    ),
    MetricSpec(
        id="total_secciones", clase="uso", titulo="Secciones",
        descripcion="Combinaciones materia × docente.", shape="scalar", unidad="conteo",
        formato="number", fuente="grades",
        medida=Measure(sql="COUNT(DISTINCT asignatura || '|' || docente)"),
        grano=["periodo", "carrera"], dim_temporal="periodo", version="v1",
    ),
    MetricSpec(
        id="total_aulas_virtuales", clase="uso", titulo="Aulas virtuales",
        descripcion="Cursos AVAC distintos.", shape="scalar", unidad="conteo",
        formato="number", fuente="course_configs",
        medida=Measure(sql="COUNT(DISTINCT codigo_avac)"),
        grano=["carrera"], version="v1",
    ),
]


def register_all() -> list[str]:
    """Registra las métricas de Core en el motor. Devuelve sus ids."""
    for m in CORE_VISTA_GENERAL:
        registry.register(m)
    return [m.id for m in CORE_VISTA_GENERAL]
