# @yachaydeep-yd/analytics-contract

El **contrato** del sistema de analítica de la casa: los tipos que el cerebro
(`yd-analytics`, Python) y la cara (`@yachaydeep-yd/dashboard`, React) comparten. Que
ambas caras dependan de este paquete es lo que evita que se desincronicen.

- `src/index.ts` — tipos TypeScript (espejo de `yd_analytics.schemas`).
- `schema/*.json` — JSON Schema generado desde los modelos Pydantic
  (`python scripts/gen_schema.py`), para validar en cualquier lenguaje.

Versionado con SemVer junto al resto del monorepo. Un cambio incompatible del
contrato es *major*.
