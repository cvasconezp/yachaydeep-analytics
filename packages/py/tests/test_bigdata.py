"""Escala / big data: el motor es agnóstico de la BD. Se prueba contra DuckDB
(motor columnar) con cientos de miles de filas — la agregación va por pushdown a la
base y solo vuelven unas pocas filas. Cambiar de Postgres a un motor columnar es solo
cambiar el Engine; el código del motor no cambia.

Se salta si duckdb no está instalado (extra opcional)."""
import pytest

pytest.importorskip("duckdb")
pytest.importorskip("duckdb_engine")

from sqlalchemy import create_engine, text  # noqa: E402

from yd_analytics import MetricQuery, registry, run_query  # noqa: E402
from yd_analytics.schemas import MetricSpec  # noqa: E402


def test_pushdown_on_columnar_engine(tmp_path):
    eng = create_engine(f"duckdb:///{tmp_path/'big.duckdb'}")
    N = 200_000
    with eng.begin() as c:
        c.execute(text(f"""CREATE TABLE big AS SELECT
            (i % 6) AS carrera_id, ('P' || (60 + (i % 6))) AS periodo,
            i AS estudiante_id, random() AS score FROM range({N}) t(i)"""))

    registry.register(MetricSpec(
        id="big_conteo", clase="dominio", titulo="Conteo big", shape="scalar", unidad="conteo",
        fuente="big", medida={"sql": "COUNT(*)"}, grano=["carrera_id", "periodo"], dim_temporal="periodo",
    ))
    r = run_query(eng, MetricQuery(metric="big_conteo", dimensions=["periodo"]))
    # 6 grupos, y la suma de los grupos == N (la agregación ocurrió en la base)
    assert len(r.result.rows) == 6
    assert sum(row["valor"] for row in r.result.rows) == N
    eng.dispose()
