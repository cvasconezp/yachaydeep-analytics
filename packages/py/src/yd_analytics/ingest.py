"""
yd_analytics.ingest — Ingesta y limpieza de archivos (Excel / CSV) → tabla analizable.

Responde a "tenemos Excel, ¿hay que limpiar antes?": sí, y este módulo lo hace en un
paso. Lee el archivo, **normaliza y limpia** (encabezados, tipos, espacios, duplicados,
formatos ecuatorianos), carga a la BD y devuelve un **perfil** con métricas y tablero
propuestos (reusa el profiler). Complementa el `yd/etl` de la casa (normalización
declarativa y reversible) — aquí una versión autocontenida para arrancar.

Requiere el extra:  pip install "yd-analytics[ingest]"   (pandas, openpyxl)
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.engine import Engine

from .profiler import ProfileResult, profile


def _slug(name: str) -> str:
    s = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9]+", "_", s.strip().lower()).strip("_")
    return s or "col"


@dataclass
class IngestReport:
    table: str
    rows_in: int
    rows_out: int
    columns: dict[str, str]              # nombre_limpio -> tipo inferido
    issues: list[str] = field(default_factory=list)
    profile: ProfileResult | None = None


def _clean(df):
    import pandas as pd

    issues: list[str] = []
    rows_in = len(df)

    # 1) Encabezados: slug único (sin acentos, snake_case).
    seen: dict[str, int] = {}
    new_cols = []
    for c in df.columns:
        base = _slug(c)
        if base in seen:
            seen[base] += 1
            base = f"{base}_{seen[base]}"
        else:
            seen[base] = 0
        new_cols.append(base)
    if list(df.columns) != new_cols:
        issues.append("encabezados normalizados (snake_case, sin acentos)")
    df.columns = new_cols

    # 2) Quitar columnas y filas totalmente vacías.
    before_cols = df.shape[1]
    df = df.dropna(axis=1, how="all")
    if df.shape[1] < before_cols:
        issues.append(f"{before_cols - df.shape[1]} columna(s) vacía(s) eliminada(s)")
    df = df.dropna(axis=0, how="all")

    def _texty(s) -> bool:   # pandas 3.0 usa dtype 'str' (no 'object') para texto
        return s.dtype == object or pd.api.types.is_string_dtype(s)

    # 3) Limpiar texto: strip; cadenas vacías → NA.
    for c in df.columns:
        if _texty(df[c]):
            df[c] = df[c].map(lambda v: v.strip() if isinstance(v, str) else v)
            df[c] = df[c].replace({"": None})

    # 4) Coerción de tipos: numérico y fecha cuando aplica (sin romper texto).
    for c in df.columns:
        if not _texty(df[c]):
            continue
        # montos con formato es-EC: "1.234,50" → 1234.50 (heurística conservadora)
        sample = df[c].dropna().astype(str)
        if len(sample) and sample.str.match(r"^-?[\d.]+,\d+$").mean() > 0.6:
            df[c] = pd.to_numeric(sample.str.replace(".", "", regex=False).str.replace(",", ".", regex=False),
                                  errors="coerce").reindex(df.index)
            issues.append(f"«{c}» convertida a número (formato es-EC)")
            continue
        num = pd.to_numeric(df[c], errors="coerce")
        if num.notna().mean() > 0.9:
            df[c] = num
            continue
        dt = pd.to_datetime(df[c], errors="coerce", format="mixed", dayfirst=True)
        if dt.notna().mean() > 0.9:
            df[c] = dt.dt.strftime("%Y-%m-%d")
            issues.append(f"«{c}» convertida a fecha (ISO)")

    # 5) Deduplicar filas exactas.
    dups = int(df.duplicated().sum())
    if dups:
        df = df.drop_duplicates()
        issues.append(f"{dups} fila(s) duplicada(s) eliminada(s)")

    return df.reset_index(drop=True), rows_in, issues


def ingest(source: str, engine: Engine, table: str, *, sheet: Any = 0) -> IngestReport:
    """Lee un Excel/CSV, lo limpia y normaliza, lo carga a `table` y lo perfila."""
    import pandas as pd

    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", table):
        raise ValueError(f"Nombre de tabla inválido: {table!r}")

    if source.lower().endswith((".xlsx", ".xlsm", ".xls")):
        df = pd.read_excel(source, sheet_name=sheet)
    else:
        df = pd.read_csv(source)

    df, rows_in, issues = _clean(df)
    df.to_sql(table, engine, if_exists="replace", index=False)

    prof = profile(engine, table)
    cols = {c.name: c.role for c in prof.columns}
    return IngestReport(table=table, rows_in=rows_in, rows_out=len(df),
                        columns=cols, issues=issues, profile=prof)
