"""
seed_demo.py — Siembra datos de ejemplo para el demo del módulo de tableros.

Crea la tabla `evaluacion_riesgo` (una fila por estudiante × periodo) con datos
deterministas (sin aleatoriedad para que el demo sea reproducible).

Uso:  python seed_demo.py
"""
from __future__ import annotations

from sqlalchemy import text

from db import get_engine

PERIODOS = ["2025-1", "2025-2", "2026-1"]
CARRERAS = ["Software", "Educación", "Enfermería", "Administración", "Contabilidad", "Diseño"]
JORNADAS = ["matutina", "nocturna"]


def _score(pi: int, ci: int, ji: int, k: int) -> float:
    """Score determinista 0..1 con estructura (algunas carreras más en riesgo)."""
    base = ((ci * 17 + ji * 7 + k * 13 + pi * 5) % 100) / 100.0
    drift = pi * 0.04            # el riesgo sube ligeramente por periodo
    carrera_bias = [0.10, 0.20, 0.05, 0.15, 0.12, 0.08][ci]
    val = min(0.99, max(0.01, 0.60 * base + drift + carrera_bias))
    return round(val, 3)


def seed() -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS evaluacion_riesgo"))
        conn.execute(text("""
            CREATE TABLE evaluacion_riesgo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                periodo TEXT NOT NULL,
                carrera TEXT NOT NULL,
                jornada TEXT NOT NULL,
                estudiante_id INTEGER NOT NULL,
                score REAL NOT NULL
            )
        """))
        rows = []
        sid = 0
        for pi, periodo in enumerate(PERIODOS):
            for ci, carrera in enumerate(CARRERAS):
                for ji, jornada in enumerate(JORNADAS):
                    n = 30 + (ci * 5) + (ji * 8)   # tamaños distintos por grupo
                    for k in range(n):
                        sid += 1
                        rows.append({
                            "periodo": periodo, "carrera": carrera,
                            "jornada": jornada, "estudiante_id": 100000 + sid,
                            "score": _score(pi, ci, ji, k),
                        })
        conn.execute(
            text("""INSERT INTO evaluacion_riesgo (periodo, carrera, jornada, estudiante_id, score)
                    VALUES (:periodo, :carrera, :jornada, :estudiante_id, :score)"""),
            rows,
        )
        total = conn.execute(text("SELECT COUNT(*) FROM evaluacion_riesgo")).scalar()
    print(f"Sembradas {total} filas en evaluacion_riesgo ({len(PERIODOS)} periodos × {len(CARRERAS)} carreras).")


if __name__ == "__main__":
    seed()
