"""
yd.analytics.registry — Carga y valida las métricas declaradas.

En producción este registro se GENERA desde docs/DATA_DICTIONARY.md (objetivo de
casa: una sola fuente de verdad). Aquí lo montamos como diccionario Python de
demostración; el contrato es idéntico.

Regla de casa: si una métrica no está en el registro, NO se grafica.
"""
from __future__ import annotations

from .schemas import MetricSpec

# --- Registro de demostración (educación / alerta temprana) ---------------- #
# fuente = vista whitelisted; medida.sql se define aquí, nunca llega del cliente.

_SPECS: dict[str, MetricSpec] = {
    m.id: m
    for m in [
        MetricSpec(
            id="total_estudiantes",
            clase="impacto",
            titulo="Estudiantes monitoreados",
            descripcion="Estudiantes con datos ingeridos en el periodo activo.",
            shape="scalar",
            unidad="conteo",
            formato="number",
            fuente="evaluacion_riesgo",
            medida={"sql": "COUNT(DISTINCT estudiante_id)"},
            grano=["periodo", "carrera", "jornada"],
            dim_temporal="periodo",
            version="v1",
        ),
        MetricSpec(
            id="estudiantes_en_riesgo",
            clase="dominio",
            titulo="Estudiantes en riesgo",
            descripcion="Estudiantes con score de deserción ≥ umbral.",
            shape="scalar",
            unidad="conteo",
            formato="number",
            fuente="evaluacion_riesgo",
            medida={
                "sql": "COUNT(DISTINCT CASE WHEN score >= :umbral THEN estudiante_id END)"
            },
            grano=["periodo", "carrera", "jornada"],
            dim_temporal="periodo",
            modelo={"nombre": "early_warning", "version": "v3"},
            roles=["docente", "coordinador", "admin"],
            version="v2",
        ),
        MetricSpec(
            id="riesgo_promedio",
            clase="dominio",
            titulo="Riesgo promedio",
            descripcion="Score de riesgo promedio (0–100).",
            shape="scalar",
            unidad="porcentaje",
            formato="percent",
            fuente="evaluacion_riesgo",
            medida={"sql": "ROUND(AVG(score) * 100, 1)"},
            grano=["periodo", "carrera", "jornada"],
            dim_temporal="periodo",
            modelo={"nombre": "early_warning", "version": "v3"},
            roles=["docente", "coordinador", "admin"],
            version="v2",
        ),
    ]
}


def get(metric_id: str) -> MetricSpec:
    if metric_id not in _SPECS:
        raise KeyError(f"Métrica no registrada: {metric_id!r}")
    return _SPECS[metric_id]


def visible_for(role: str) -> list[MetricSpec]:
    """Métricas que un rol puede ver (autorización por métrica, §5)."""
    return [s for s in _SPECS.values() if "*" in s.roles or role in s.roles]


def all_ids() -> list[str]:
    return list(_SPECS)
