"""Modelo semántico automático: detección de relaciones y consulta cruzando tablas."""
from sqlalchemy import create_engine, text

from yd_analytics.model import build_model, detect_relationships, query_related


def _db(tmp_path):
    eng = create_engine(f"sqlite:///{tmp_path/'m.db'}")
    with eng.begin() as c:
        c.execute(text("CREATE TABLE carreras(id INTEGER, nombre TEXT)"))
        c.execute(text("INSERT INTO carreras VALUES (1,'Software'),(2,'Educación'),(3,'Enfermería')"))
        c.execute(text("CREATE TABLE jornadas(id INTEGER, nombre TEXT)"))
        c.execute(text("INSERT INTO jornadas VALUES (1,'Matutina'),(2,'Nocturna')"))
        c.execute(text("CREATE TABLE estudiantes(id INTEGER, nombre TEXT, carrera_id INTEGER, jornada_id INTEGER)"))
        c.execute(text("""INSERT INTO estudiantes VALUES
            (1,'Ana',1,1),(2,'Luis',1,2),(3,'Eva',2,1),(4,'Beto',2,2),(5,'Sol',3,1),(6,'Iván',1,1)"""))
    return eng


def test_detect_foreign_keys(tmp_path):
    eng = _db(tmp_path)
    rels = detect_relationships(eng, ["estudiantes", "carreras", "jornadas"])
    pairs = {(r.from_table, r.from_col, r.to_table, r.to_col) for r in rels}
    assert ("estudiantes", "carrera_id", "carreras", "id") in pairs
    assert ("estudiantes", "jornada_id", "jornadas", "id") in pairs


def test_query_across_tables_without_sql(tmp_path):
    eng = _db(tmp_path)
    model = build_model(eng, ["estudiantes", "carreras", "jornadas"])
    # "cuenta estudiantes por nombre de carrera" — el JOIN lo arma el modelo
    rows = query_related(eng, model, fact="estudiantes", measure="COUNT(*)",
                         dimension="nombre", dim_table="carreras")
    by = {r["nombre"]: r["valor"] for r in rows}
    assert by["Software"] == 3 and by["Educación"] == 2 and by["Enfermería"] == 1


def test_query_no_relation_raises(tmp_path):
    eng = _db(tmp_path)
    model = build_model(eng, ["estudiantes", "carreras"])
    import pytest
    with pytest.raises(ValueError):
        query_related(eng, model, fact="estudiantes", measure="COUNT(*)",
                      dimension="nombre", dim_table="jornadas")  # no está en el modelo
