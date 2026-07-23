"""
yd_analytics.export — Exportación de resultados (CSV). PNG se hace en el frontend
(ECharts getDataURL). El CSV exporta los AGREGADOS mostrados, nunca filas crudas.
"""
from __future__ import annotations

import csv
import io

from .schemas import MetricResult


def to_csv(result: MetricResult) -> str:
    """Serializa un MetricResult a CSV (encabezado = columnas; una fila por dato)."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(result.columns)
    for r in result.rows:
        w.writerow([r.get(c, "") for c in result.columns])
    return buf.getvalue()
