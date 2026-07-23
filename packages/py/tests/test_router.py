import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from yd_analytics import make_router  # noqa: E402


def _client(engine):
    app = FastAPI()
    app.include_router(make_router(get_engine=lambda: engine))
    return TestClient(app)


def test_registry_endpoint(engine):
    c = _client(engine)
    r = c.get("/analytics/registry", headers={"X-Demo-Role": "docente"})
    assert r.status_code == 200
    assert any(m["id"] == "estudiantes_en_riesgo" for m in r.json())


def test_query_endpoint(engine):
    c = _client(engine)
    r = c.post("/analytics/query",
               json={"metric": "estudiantes_en_riesgo", "dimensions": ["carrera"],
                     "params": {"umbral": 0.4}},
               headers={"X-Demo-Role": "coordinador"})
    assert r.status_code == 200
    body = r.json()
    assert body["chart"]["type"] in ("bar", "bar_h")
    assert "rows" in body["result"]


def test_forbidden_and_404(engine):
    c = _client(engine)
    assert c.post("/analytics/query", json={"metric": "estudiantes_en_riesgo"},
                  headers={"X-Demo-Role": "invitado"}).status_code == 403
    assert c.post("/analytics/query", json={"metric": "nope"}).status_code == 404


def test_graph_endpoint(engine):
    c = _client(engine)
    r = c.post("/analytics/graph/malla_prerrequisitos", json={"filters": []},
               headers={"X-Demo-Role": "admin"})
    assert r.status_code == 200
    assert len(r.json()["nodes"]) == 4


def test_assist_endpoint(engine):
    c = _client(engine)
    r = c.post("/analytics/assist", json={"question": "estudiantes en riesgo por carrera"},
               headers={"X-Demo-Role": "coordinador"})
    assert r.status_code == 200
    body = r.json()
    assert body["suggestion"]["metric"] == "estudiantes_en_riesgo"
    assert body["suggestion"]["dimensions"] == ["carrera"]
    assert body["chart"]["type"] in ("bar", "bar_h")
