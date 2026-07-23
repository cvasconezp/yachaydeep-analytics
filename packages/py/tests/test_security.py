"""#3 Seguridad de datos cifrados: índice ciego, k-anonimato, hook de descifrado."""
from sqlalchemy import text

from yd_analytics import MetricQuery, registry, run_query
from yd_analytics.schemas import MetricSpec


def _setup(engine):
    # Tabla con columna de ÍNDICE CIEGO (socio_bidx = hash) — sin texto plano.
    with engine.begin() as c:
        c.execute(text("DROP TABLE IF EXISTS aportes"))
        c.execute(text("CREATE TABLE aportes(socio_bidx TEXT, monto REAL)"))
        rows = ([{"socio_bidx": "h_ana", "monto": 10}] * 5 +
                [{"socio_bidx": "h_luis", "monto": 20}] * 4 +
                [{"socio_bidx": "h_eva", "monto": 5}] * 2)   # grupo pequeño (2 < k=3)
        c.execute(text("INSERT INTO aportes(socio_bidx,monto) VALUES(:socio_bidx,:monto)"), rows)
    registry.register(MetricSpec(
        id="aportes_por_socio", clase="dominio", titulo="Aportes por socio", shape="scalar",
        unidad="conteo", fuente="aportes", medida={"sql": "COUNT(*)"}, grano=["socio"],
        blind_index={"socio": "socio_bidx"}, k_anon=3,
    ))


def test_blind_index_groups_by_hash(engine):
    _setup(engine)
    r = run_query(engine, MetricQuery(metric="aportes_por_socio", dimensions=["socio"]))
    labels = {row["socio"] for row in r.result.rows}
    # se agrupó por el hash (índice ciego), la etiqueta ES el hash, no texto plano
    assert labels <= {"h_ana", "h_luis"}          # h_eva (2) suprimido por k-anon
    assert "h_eva" not in labels


def test_k_anonymity_suppresses_small_groups(engine):
    _setup(engine)
    r = run_query(engine, MetricQuery(metric="aportes_por_socio", dimensions=["socio"]))
    assert r.result.meta["k_anon_suprimidas"] == 1   # el grupo de 2 se ocultó


def test_decrypt_labels_hook(engine):
    _setup(engine)
    tabla = {"h_ana": "Ana", "h_luis": "Luis"}
    r = run_query(engine, MetricQuery(metric="aportes_por_socio", dimensions=["socio"]),
                  decrypt_labels=lambda dim, hashes: {h: tabla.get(h, h) for h in hashes})
    labels = {row["socio"] for row in r.result.rows}
    assert labels == {"Ana", "Luis"}                 # hash → texto, solo lo visible
