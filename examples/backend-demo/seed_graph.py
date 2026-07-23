"""
seed_graph.py — Malla curricular (prerrequisitos) para el demo del grafo de nodos.

Crea dos tablas whitelisted por el GraphSpec:
  asignatura(codigo, nombre, nivel, carrera)
  prerrequisito(requiere, asignatura, carrera)   # requiere → asignatura (dirigido)

Uso:  python seed_graph.py
"""
from __future__ import annotations

from sqlalchemy import text

from db import get_engine

CARRERA = "Software"

# (codigo, nombre, nivel)
ASIGNATURAS = [
    ("MAT101", "Matemática Básica", 1),
    ("PRG101", "Introducción a la Programación", 1),
    ("COM101", "Comunicación Oral y Escrita", 1),
    ("ALG101", "Álgebra Lineal", 1),
    ("MAT201", "Cálculo I", 2),
    ("PRG201", "Programación I", 2),
    ("FIS201", "Física I", 2),
    ("DIS201", "Estructuras Discretas", 2),
    ("MAT301", "Cálculo II", 3),
    ("EST301", "Estadística y Probabilidad", 3),
    ("PRG301", "Programación Orientada a Objetos", 3),
    ("PRG302", "Estructuras de Datos", 3),
    ("BDD301", "Bases de Datos I", 3),
    ("PRG401", "Algoritmos", 4),
    ("SOP401", "Sistemas Operativos", 4),
    ("BDD401", "Bases de Datos II", 4),
    ("RED401", "Redes de Computadoras", 4),
    ("ISW501", "Ingeniería de Software", 5),
    ("IA501", "Inteligencia Artificial", 5),
    ("WEB501", "Desarrollo Web", 5),
    ("ARQ501", "Arquitectura de Software", 5),
    ("ML601", "Machine Learning", 6),
    ("SEG601", "Seguridad Informática", 6),
    ("TIT601", "Proyecto de Titulación", 6),
]

# (requiere, asignatura)  -> "requiere" es prerrequisito de "asignatura"
PRERREQUISITOS = [
    ("MAT101", "MAT201"), ("PRG101", "PRG201"), ("MAT101", "FIS201"),
    ("ALG101", "FIS201"), ("MAT101", "DIS201"),
    ("MAT201", "MAT301"), ("MAT201", "EST301"), ("PRG201", "PRG301"),
    ("PRG201", "PRG302"), ("DIS201", "PRG302"), ("PRG201", "BDD301"),
    ("PRG302", "PRG401"), ("MAT301", "PRG401"), ("PRG302", "SOP401"),
    ("BDD301", "BDD401"), ("FIS201", "RED401"), ("PRG302", "RED401"),
    ("PRG301", "ISW501"), ("BDD301", "ISW501"), ("PRG401", "IA501"),
    ("EST301", "IA501"), ("PRG301", "WEB501"), ("BDD301", "WEB501"),
    ("PRG301", "ARQ501"), ("SOP401", "ARQ501"),
    ("IA501", "ML601"), ("EST301", "ML601"), ("RED401", "SEG601"),
    ("SOP401", "SEG601"), ("ISW501", "TIT601"), ("BDD401", "TIT601"),
    ("WEB501", "TIT601"),
]


def seed() -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS asignatura"))
        conn.execute(text("DROP TABLE IF EXISTS prerrequisito"))
        conn.execute(text("""
            CREATE TABLE asignatura (
                codigo TEXT PRIMARY KEY, nombre TEXT NOT NULL,
                nivel INTEGER NOT NULL, carrera TEXT NOT NULL)
        """))
        conn.execute(text("""
            CREATE TABLE prerrequisito (
                requiere TEXT NOT NULL, asignatura TEXT NOT NULL, carrera TEXT NOT NULL)
        """))
        conn.execute(
            text("INSERT INTO asignatura (codigo, nombre, nivel, carrera) VALUES (:c,:n,:l,:k)"),
            [{"c": c, "n": n, "l": l, "k": CARRERA} for c, n, l in ASIGNATURAS],
        )
        conn.execute(
            text("INSERT INTO prerrequisito (requiere, asignatura, carrera) VALUES (:r,:a,:k)"),
            [{"r": r, "a": a, "k": CARRERA} for r, a in PRERREQUISITOS],
        )
    print(f"Sembradas {len(ASIGNATURAS)} asignaturas y {len(PRERREQUISITOS)} prerrequisitos.")


if __name__ == "__main__":
    seed()
