"""Fixtures: un engine SQLite temporal sembrado con datos mínimos para las pruebas."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text


@pytest.fixture()
def engine(tmp_path):
    eng = create_engine(f"sqlite:///{tmp_path/'t.db'}")
    with eng.begin() as c:
        # tabla tabular
        c.execute(text("""CREATE TABLE evaluacion_riesgo(
            id INTEGER PRIMARY KEY, periodo TEXT, carrera TEXT, jornada TEXT,
            estudiante_id INTEGER, score REAL)"""))
        rows = []
        sid = 0
        for pi, per in enumerate(["2025-1", "2025-2", "2026-1"]):
            for carr in ["Software", "Educación", "Enfermería"]:
                for jor in ["matutina", "nocturna"]:
                    for k in range(10):
                        sid += 1
                        score = round(((pi * 7 + k * 3 + len(carr)) % 100) / 100.0, 3)
                        rows.append({"periodo": per, "carrera": carr, "jornada": jor,
                                     "estudiante_id": 1000 + sid, "score": score})
        c.execute(text("""INSERT INTO evaluacion_riesgo(periodo,carrera,jornada,estudiante_id,score)
            VALUES(:periodo,:carrera,:jornada,:estudiante_id,:score)"""), rows)
        # tablas de grafo
        c.execute(text("CREATE TABLE asignatura(codigo TEXT, nombre TEXT, nivel INTEGER, carrera TEXT)"))
        c.execute(text("CREATE TABLE prerrequisito(requiere TEXT, asignatura TEXT, carrera TEXT)"))
        asigs = [("MAT101", "Matemática", 1), ("PRG101", "Programación I", 1),
                 ("PRG201", "Estructuras", 2), ("BDD301", "Bases de Datos", 3)]
        c.execute(text("INSERT INTO asignatura VALUES(:c,:n,:l,'Software')"),
                  [{"c": a, "n": b, "l": d} for a, b, d in asigs])
        c.execute(text("INSERT INTO prerrequisito VALUES(:r,:a,'Software')"),
                  [{"r": "MAT101", "a": "PRG201"}, {"r": "PRG101", "a": "PRG201"},
                   {"r": "PRG201", "a": "BDD301"}])
    return eng
