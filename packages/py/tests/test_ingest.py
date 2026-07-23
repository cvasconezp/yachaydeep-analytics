"""Ingesta y limpieza de un archivo 'sucio' (Excel/CSV) → tabla + perfil."""
import pytest

pytest.importorskip("pandas")

from sqlalchemy import create_engine, text  # noqa: E402

from yd_analytics import ingest  # noqa: E402


def _messy_csv(path):
    # Encabezados con acentos/espacios, tipos mezclados, vacíos, duplicados, monto es-EC.
    path.write_text(
        "Nombre Completo, Carrera ,Monto Aporte,Fecha Registro,Vacía\n"
        "  Ana Pérez ,Software,\"1.234,50\",01/03/2026,\n"
        "Luis Gómez,Educación,\"980,00\",15/03/2026,\n"
        "Luis Gómez,Educación,\"980,00\",15/03/2026,\n"   # duplicado exacto
        "Eva Díaz ,Enfermería,\"1.050,25\",02/04/2026,\n",
        encoding="utf-8",
    )
    return str(path)


def test_ingest_cleans_and_profiles(tmp_path):
    src = _messy_csv(tmp_path / "aportes.csv")
    eng = create_engine(f"sqlite:///{tmp_path/'out.db'}")
    rep = ingest(src, eng, "aportes")

    # encabezados normalizados (snake_case, sin acentos)
    assert "nombre_completo" in rep.columns
    assert "monto_aporte" in rep.columns
    # duplicado eliminado: 4 filas → 3
    assert rep.rows_in == 4 and rep.rows_out == 3
    # columna vacía eliminada
    assert "vacia" not in rep.columns
    # monto es-EC convertido a número (se verifica con la SUMA más abajo)
    # se generó un tablero propuesto
    assert rep.profile is not None
    assert rep.profile.dashboard["titulo"].startswith("Tablero automático")
    # los datos quedaron en la tabla y son consultables
    with eng.connect() as c:
        total = c.execute(text("SELECT COUNT(*) FROM aportes")).scalar()
        suma = c.execute(text("SELECT ROUND(SUM(monto_aporte),2) FROM aportes")).scalar()
    assert total == 3
    assert abs(suma - (1234.50 + 980.00 + 1050.25)) < 0.01
