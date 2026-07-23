"""Multi-tenant: aislamiento por inquilino y resolución por subdominio."""
import pytest
from sqlalchemy import text

from yd_analytics.tenancy import (
    TenantResolver, make_get_engine, row_filter, tenant_from_host,
)


def test_engine_isolation_per_tenant(tmp_path):
    res = TenantResolver()
    res.register_dsn("kullki", f"sqlite:///{tmp_path/'kullki.db'}", plan="pro")
    res.register_dsn("ancora", f"sqlite:///{tmp_path/'ancora.db'}", plan="free")
    with res.engine_for("kullki").begin() as c:
        c.execute(text("CREATE TABLE t(x INT)")); c.execute(text("INSERT INTO t VALUES (100)"))
    with res.engine_for("ancora").begin() as c:
        c.execute(text("CREATE TABLE t(x INT)")); c.execute(text("INSERT INTO t VALUES (7)"))
    # cada inquilino ve SOLO sus datos
    assert res.engine_for("kullki").connect().execute(text("SELECT x FROM t")).scalar() == 100
    assert res.engine_for("ancora").connect().execute(text("SELECT x FROM t")).scalar() == 7
    assert res.get("kullki").plan == "pro"


def test_make_get_engine_resolves_current_tenant(tmp_path):
    res = TenantResolver()
    res.register_dsn("core", f"sqlite:///{tmp_path/'core.db'}")
    current = {"id": "core"}
    get_engine = make_get_engine(res, lambda: current["id"])
    assert get_engine() is res.engine_for("core")


def test_tenant_from_host():
    assert tenant_from_host("kullki.analytics.yachaydeep.com") == "kullki"
    assert tenant_from_host("ancora.analytics.yachaydeep.com:443") == "ancora"
    assert tenant_from_host("analytics.yachaydeep.com") is None       # dominio base = landing


def test_row_filter_safe():
    assert row_filter("kullki") == "tenant_id = 'kullki'"
    with pytest.raises(ValueError):
        row_filter("a'; DROP TABLE x;--")
