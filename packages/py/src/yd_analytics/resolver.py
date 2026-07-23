"""
yd.analytics.resolver — El "Show Me" de la casa: forma → ChartSpec.

Determinista: la misma forma (y cardinalidad) produce siempre el mismo gráfico.
Corre DESPUÉS del motor para poder mirar la cardinalidad real de los datos.
Ver docs/DASHBOARD.md §2.
"""
from __future__ import annotations

from .schemas import (
    ChartSpec, Encoding, Interactions, MetricQuery, MetricResult, MetricSpec,
)

_CARD_MAX_VERTICAL = 8   # ≤ 8 categorías → barras verticales; más → horizontales Top-N


def resolve(spec: MetricSpec, query: MetricQuery, result: MetricResult) -> ChartSpec:
    if query.chart_hint:                      # override explícito del autor
        return _from_hint(spec, query, result)

    shape = result.shape
    dims = query.dimensions

    if shape == "scalar":
        return ChartSpec(
            type="kpi",
            encoding={"value": Encoding(field="valor", type="quantitative",
                                        format=spec.formato)},
            series_role="accent",
        )

    if shape == "timeseries":
        d = dims[0]
        area = spec.unidad in ("conteo", "moneda")
        return ChartSpec(
            type="area" if area else "line",
            encoding={
                "x": Encoding(field=d, type="temporal"),
                "y": Encoding(field="valor", type="quantitative", format=spec.formato),
            },
            interactions=Interactions(tooltip=[d, "valor"]),
        )

    if shape == "category":
        d = dims[0]
        wide = len(result.rows) > _CARD_MAX_VERTICAL
        note = None
        if result.truncated:
            note = (f"Mostrando {result.truncated.shown} de {result.truncated.total}; "
                    f"resto en «{result.truncated.grouped_as}».")
        return ChartSpec(
            type="bar_h" if wide else "bar",
            encoding={
                "x": Encoding(field=d, type="nominal"),
                "y": Encoding(field="valor", type="quantitative", format=spec.formato),
            },
            interactions=Interactions(
                emits_filter=d,               # clic → filtra el tablero (cross-filter)
                drilldown=_drill_after(spec, d),
                tooltip=[d, "valor"],
            ),
            note=note,
        )

    if shape == "timeseries_multi":
        t = spec.dim_temporal
        cat = next(x for x in dims if x != t)
        return ChartSpec(
            type="line",
            encoding={
                "x": Encoding(field=t, type="temporal"),
                "y": Encoding(field="valor", type="quantitative", format=spec.formato),
                "series": Encoding(field=cat, type="nominal"),
            },
            interactions=Interactions(emits_filter=cat, tooltip=[t, cat, "valor"]),
        )

    if shape == "matrix":
        return ChartSpec(
            type="heatmap",
            encoding={
                "x": Encoding(field=dims[0], type="nominal"),
                "y": Encoding(field=dims[1], type="nominal"),
                "value": Encoding(field="valor", type="quantitative", format=spec.formato),
            },
            interactions=Interactions(tooltip=[dims[0], dims[1], "valor"]),
        )

    # fallback seguro
    return ChartSpec(
        type="table",
        encoding={c: Encoding(field=c, type="nominal") for c in result.columns},
    )


def _drill_after(spec: MetricSpec, current: str) -> list[str]:
    """Jerarquía de drill: lo que queda del grano tras la dimensión actual."""
    rest = [d for d in spec.grano if d != current and d != spec.dim_temporal]
    return [current, *rest] if rest else []


def _from_hint(spec, query, result) -> ChartSpec:
    d = query.dimensions[0] if query.dimensions else None
    enc = {}
    if d:
        enc["x"] = Encoding(field=d, type="nominal")
    enc["y"] = Encoding(field="valor", type="quantitative", format=spec.formato)
    tooltip = ([d] if d else []) + ["valor"]
    return ChartSpec(
        type=query.chart_hint,
        encoding=enc,
        interactions=Interactions(emits_filter=d, tooltip=tooltip),
    )
