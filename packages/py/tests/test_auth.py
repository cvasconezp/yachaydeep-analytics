import pytest

from yd_analytics.auth import ApiKey, allowed_origins, load_keys, match_key, parse_keys

fastapi = pytest.importorskip("fastapi")
from fastapi import Depends, FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from yd_analytics import make_auth, make_router  # noqa: E402


# ---------------------------------------------------------------- funciones puras
def test_parse_keys_formatos():
    ks = parse_keys("k1:tenantA:admin, k2:tenantB, k3")
    assert ks["k1"] == ApiKey("k1", "tenantA", "admin")
    assert ks["k2"] == ApiKey("k2", "tenantB", "admin")   # rol por defecto
    assert ks["k3"] == ApiKey("k3", "default", "admin")   # tenant y rol por defecto
    assert parse_keys("") == {} and parse_keys(None) == {}


def test_match_key_constante():
    ks = parse_keys("secreta:t1:viewer")
    assert match_key(ks, "secreta") == ApiKey("secreta", "t1", "viewer")
    assert match_key(ks, "otra") is None
    assert match_key(ks, None) is None
    assert match_key({}, "cualquiera") is None


def test_allowed_origins(monkeypatch):
    monkeypatch.delenv("YD_ALLOWED_ORIGINS", raising=False)
    assert allowed_origins(dev_open=True) == ["*"]
    assert allowed_origins(dev_open=False) == []          # cerrado: exige declararlos
    monkeypatch.setenv("YD_ALLOWED_ORIGINS", "https://a.com, https://b.com")
    assert allowed_origins(dev_open=False) == ["https://a.com", "https://b.com"]


def test_load_keys_env(monkeypatch):
    monkeypatch.setenv("YD_API_KEYS", "envkey:tEnv:admin")
    assert load_keys()["envkey"].tenant == "tEnv"


# ---------------------------------------------------------------- dependencia FastAPI
def _app(**auth_kwargs):
    auth = make_auth(**auth_kwargs)
    app = FastAPI()

    @app.get("/quien", dependencies=[Depends(auth.get_principal)])
    def quien(tenant: str = Depends(auth.get_tenant), role: str = Depends(auth.get_role)):
        return {"tenant": tenant, "role": role}

    return app, auth


def test_modo_abierto_sin_llaves():
    app, auth = _app(keys={}, require=False)
    assert auth.require is False
    c = TestClient(app)
    r = c.get("/quien")                       # sin llave, pero abierto
    assert r.status_code == 200
    assert r.json() == {"tenant": "default", "role": "admin"}


def test_modo_cerrado_exige_llave():
    keys = parse_keys("clave-buena:acme:viewer")
    app, auth = _app(keys=keys, require=True)
    assert auth.require is True
    c = TestClient(app)
    # Sin llave -> 401
    assert c.get("/quien").status_code == 401
    # Llave inválida -> 403
    assert c.get("/quien", headers={"X-API-Key": "mala"}).status_code == 403
    # Llave válida por header X-API-Key -> 200 + rol/tenant resueltos
    r = c.get("/quien", headers={"X-API-Key": "clave-buena"})
    assert r.status_code == 200 and r.json() == {"tenant": "acme", "role": "viewer"}
    # También por Authorization: Bearer
    r2 = c.get("/quien", headers={"Authorization": "Bearer clave-buena"})
    assert r2.status_code == 200 and r2.json()["tenant"] == "acme"


def test_router_usa_rol_de_la_apikey(engine):
    """La API key define el rol con el que el router filtra métricas."""
    keys = parse_keys("k-coord:acme:coordinador, k-guest:acme:invitado")
    auth = make_auth(keys=keys, require=True)
    app = FastAPI()
    app.include_router(make_router(get_engine=lambda: engine, get_role=auth.get_role))
    c = TestClient(app)
    # coordinador puede consultar
    r = c.post("/analytics/query",
               json={"metric": "estudiantes_en_riesgo", "dimensions": ["carrera"],
                     "params": {"umbral": 0.4}},
               headers={"X-API-Key": "k-coord"})
    assert r.status_code == 200
    # invitado -> 403 por rol
    r2 = c.post("/analytics/query", json={"metric": "estudiantes_en_riesgo"},
                headers={"X-API-Key": "k-guest"})
    assert r2.status_code == 403
    # sin llave -> 401
    r3 = c.post("/analytics/query", json={"metric": "estudiantes_en_riesgo"})
    assert r3.status_code == 401
