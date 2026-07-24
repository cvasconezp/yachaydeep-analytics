"""Telemetría de producto: ingesta de eventos + métricas de uso con el mismo motor."""
from __future__ import annotations

from datetime import datetime, timezone

from yd_analytics import MetricQuery, run_query, telemetry


def _seed(engine):
    telemetry.ensure_events_table(engine)
    evs = []
    dias = ["2026-07-20", "2026-07-21", "2026-07-22"]
    productos = ["core", "ancora", "kullki"]
    for di, dia in enumerate(dias):
        for pi, prod in enumerate(productos):
            # 6 usuarios por producto/día (supera k=5), en 2 dispositivos
            for u in range(6):
                disp = "mobile" if u % 2 else "desktop"
                evs.append(telemetry.Event(
                    producto=prod, evento="pageview",
                    pantalla=f"/{prod}/inicio" if u % 3 else f"/{prod}/reportes",
                    usuario_id=f"{prod}-u{u}", sesion_id=f"{prod}-{dia}-u{u}",
                    dispositivo=disp, os="android" if disp == "mobile" else "windows",
                    pais="EC", ts=datetime(2026, 7, 20 + di, 10, 0, tzinfo=timezone.utc),
                ))
    n = telemetry.record_events(engine, evs, tenant="default")
    return n


def test_ingest_and_register(engine):
    n = _seed(engine)
    assert n == 3 * 3 * 6  # días * productos * usuarios
    ids = telemetry.register_telemetry()
    assert "uso_usuarios_activos" in ids


def test_active_users_scalar(engine):
    _seed(engine); telemetry.register_telemetry()
    r = run_query(engine, MetricQuery(metric="uso_usuarios_activos"))
    assert r.result.shape == "scalar"
    assert r.chart.type == "kpi"
    # 6 usuarios distintos por producto * 3 productos = 18 seudónimos únicos
    assert r.result.rows[0]["valor"] == 18


def test_usage_timeseries(engine):
    _seed(engine); telemetry.register_telemetry()
    r = run_query(engine, MetricQuery(metric="uso_usuarios_por_dia", dimensions=["dia"]))
    assert r.result.shape == "timeseries"
    assert r.chart.type in ("line", "area")
    assert len(r.result.rows) == 3  # tres días


def test_top_screens_category(engine):
    _seed(engine); telemetry.register_telemetry()
    r = run_query(engine, MetricQuery(metric="uso_top_pantallas", dimensions=["pantalla"]))
    assert r.result.shape == "category"
    assert r.chart.type in ("bar", "bar_h")
    assert len(r.result.rows) >= 1


def test_by_device(engine):
    _seed(engine); telemetry.register_telemetry()
    r = run_query(engine, MetricQuery(metric="uso_por_dispositivo", dimensions=["dispositivo"]))
    assert r.result.shape == "category"
    devices = {row["dispositivo"] for row in r.result.rows}
    assert devices <= {"desktop", "mobile"}
