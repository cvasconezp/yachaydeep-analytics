"""
gen_schema.py — Genera los JSON Schema del contrato desde los modelos Pydantic
del paquete yd_analytics. La fuente de verdad del contrato son los modelos; este
script materializa los .json que consumen otros lenguajes.

Uso:  python scripts/gen_schema.py
"""
from __future__ import annotations

import json
import pathlib

from yd_analytics import schemas as S

OUT = pathlib.Path(__file__).resolve().parents[1] / "packages" / "contract" / "schema"

MODELS = [
    S.MetricSpec, S.MetricQuery, S.MetricResult, S.ChartSpec, S.PanelResponse,
    S.Filter, S.GraphSpec, S.GraphNode, S.GraphEdge, S.GraphResult,
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    index = {}
    for m in MODELS:
        schema = m.model_json_schema()
        path = OUT / f"{m.__name__}.schema.json"
        path.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        index[m.__name__] = f"schema/{m.__name__}.schema.json"
    (OUT / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generados {len(MODELS)} esquemas en {OUT}")


if __name__ == "__main__":
    main()
