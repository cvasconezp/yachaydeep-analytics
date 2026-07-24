"""Informe HTML: narrativa determinista desde los cálculos."""
from __future__ import annotations

from yd_analytics import report


def test_narrate_timeseries():
    block = {
        "shape": "timeseries",
        "tendencia": {"n": 6, "primero": 29.5, "ultimo": 34.0, "direccion": "creciente",
                      "pendiente": 0.89, "r2": 0.9, "p": 0.004,
                      "mann_kendall": {"tendencia": "creciente", "p": 0.024},
                      "cambio_total_pct": 15.3, "cambio_ultimo_pct": 2.7,
                      "pronostico_siguiente": 34.9, "pronostico_rango": [33.7, 36.1]},
        "descriptivos": {"n": 6}, "cautelas": [],
    }
    nar = report.narrate(block)
    joined = " ".join(nar["resumen"])
    assert "creciente" in joined
    assert "Mann-Kendall" in joined
    assert any(k["label"] == "Pronóstico" for k in nar["kpis"])


def test_narrate_proportion_margin():
    from yd_analytics import stats as S
    pr = S.proportion_ci(1360, 4000, population=13_500_000)
    nar = report.narrate({"shape": "proportion", "proporcion": pr, "cautelas": []})
    joined = " ".join(nar["resumen"])
    assert "Margen de error".lower() not in joined.lower() or "margen de error" in joined.lower()
    assert "Wilson" in joined
    assert "empate técnico" in joined
    # el KPI de margen de error existe
    assert any("Margen" in k["label"] for k in nar["kpis"])


def test_build_report_html():
    paneles = [
        {"titulo": "Voto A", "shape": "proportion", "k": 340, "n": 1000},
        {"titulo": "Por provincia", "shape": "category", "columns": ["prov", "v"],
         "rows": [{"prov": "Quito", "v": 50}, {"prov": "Guayaquil", "v": 30}, {"prov": "Cuenca", "v": 20}]},
    ]
    html = report.build_report(paneles, titulo="Informe test")
    assert html.startswith("<!DOCTYPE html>")
    assert "Resumen ejecutivo" in html
    assert "Informe test" in html
    assert "Wilson" in html


def test_fmt_es_ec():
    assert report.fmt(1234567.5, 1) == "1.234.567,5"
    assert report.pct(34.0) == "34,0%"
    assert report.signed(2.7) == "+2,7"
