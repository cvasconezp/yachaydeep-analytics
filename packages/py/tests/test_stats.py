"""Estadística real: se verifica contra valores conocidos (exactitud)."""
from __future__ import annotations

import math

import pytest

from yd_analytics import stats as S


def test_describe_known_values():
    d = S.describe([2, 4, 4, 4, 5, 5, 7, 9])
    assert d["n"] == 8
    assert d["media"] == pytest.approx(5.0)
    assert d["mediana"] == pytest.approx(4.5)
    assert d["std"] == pytest.approx(2.13809, abs=1e-4)     # muestral (ddof=1)
    assert d["min"] == 2 and d["max"] == 9 and d["rango"] == 7
    assert d["percentiles"]["p50"] == pytest.approx(4.5)


def test_ci_mean_contains_mean():
    d = S.describe(list(range(1, 101)))
    lo, hi = d["ic95_media"]
    assert lo < d["media"] < hi


def test_proportion_moe_and_wilson():
    r = S.proportion_ci(340, 1000)
    assert r["p"] == pytest.approx(0.34)
    # MoE normal = 1.96*sqrt(.34*.66/1000) = 2.936%
    assert r["margen_error_pct"] == pytest.approx(2.936, abs=1e-2)
    lo, hi = r["wilson"]
    assert lo < 0.34 < hi
    assert 0 <= lo and hi <= 1


def test_proportion_finite_population_shrinks_moe():
    big = S.proportion_ci(340, 1000)["margen_error"]
    small = S.proportion_ci(340, 1000, population=2000)["margen_error"]
    assert small < big  # corrección por población finita reduce el margen


def test_sample_size_for_moe():
    assert S.sample_size_for_moe(0.03)["n"] == 1068     # p=0.5, 95%
    assert S.sample_size_for_moe(0.05)["n"] == 385


def test_trend_perfect_line():
    t = S.trend([10, 12, 14, 16, 18, 20])
    assert t["pendiente"] == pytest.approx(2.0)
    assert t["r2"] == pytest.approx(1.0)
    assert t["direccion"] == "creciente"
    assert t["cambio_ultimo_abs"] == pytest.approx(2.0)


def test_mann_kendall_monotonic():
    assert S.mann_kendall([1, 2, 3, 4, 5, 6, 7, 8])["tendencia"] == "creciente"
    assert S.mann_kendall([8, 7, 6, 5, 4, 3, 2, 1])["tendencia"] == "decreciente"


def test_correlation_perfect():
    c = S.correlation([1, 2, 3, 4, 5], [2, 4, 6, 8, 10])
    assert c["pearson_r"] == pytest.approx(1.0)
    assert c["spearman_rho"] == pytest.approx(1.0)
    assert c["significativa"] is True


def test_outliers_iqr():
    o = S.outliers([1, 2, 3, 4, 5, 6, 7, 8, 9, 100])
    assert o["iqr"]["n"] >= 1                # 100 es atípico
    assert 100.0 in o["iqr"]["valores"]


def test_categorical_concentration_and_chi2():
    c = S.categorical_summary(["A", "B", "C", "D"], [50, 25, 15, 10])
    assert c["lider"]["label"] == "A"
    assert c["lider"]["share_pct"] == pytest.approx(50.0)
    assert c["chi2_uniformidad"]["uniforme"] is False
    # uniforme perfecto
    u = S.categorical_summary(["A", "B", "C", "D"], [25, 25, 25, 25])
    assert u["chi2_uniformidad"]["uniforme"] is True
    assert u["hhi_norm"] == pytest.approx(0.0, abs=1e-9)


def test_chi_square_independence_cramers_v():
    # asociación fuerte (diagonal)
    r = S.chi_square_independence([[40, 5], [5, 40]])
    assert r["asociacion_significativa"] is True
    assert 0 <= r["cramers_v"] <= 1


def test_compare_groups_anova_kruskal():
    r = S.compare_groups({
        "a": [10, 11, 9, 10, 10], "b": [10, 11, 9, 10, 10], "c": [20, 21, 19, 20, 20]})
    assert r["anova"]["significativo"] is True
    assert r["kruskal"]["significativo"] is True
    assert r["efecto"] in ("pequeño", "medio", "grande")


def test_summarize_timeseries_and_category():
    ts = S.summarize_result("timeseries",
                            [{"dia": f"2026-01-0{i}", "valor": v} for i, v in enumerate([10, 12, 14, 16, 18], 1)],
                            ["dia", "valor"])
    assert ts["tendencia"]["direccion"] == "creciente"
    cat = S.summarize_result("category",
                             [{"ciudad": c, "valor": v} for c, v in [("Quito", 50), ("Guayaquil", 30), ("Cuenca", 20)]],
                             ["ciudad", "valor"])
    assert cat["categorico"]["lider"]["label"] == "Quito"


def test_small_sample_caution():
    out = S.summarize_result("category",
                             [{"c": "A", "v": 3}, {"c": "B", "v": 2}], ["c", "v"])
    assert any("pequeña" in c.lower() for c in out["cautelas"])
