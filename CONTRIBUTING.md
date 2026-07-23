# Contribuir

Regla de oro (como en `@yachaydeep/brand`): **la lógica y el contrato viven en el
paquete y se propagan por versión; nunca se bifurcan en un consumidor.**

## Desarrollo

```bash
# Python (cerebro)
cd packages/py && pip install -e .[dev] && pytest

# JS (contrato + cara)
npm install
npm run build           # compila contract y dashboard
npm run typecheck

# Regenerar JSON Schema tras cambiar los modelos Pydantic
npm run schema
```

## Reglas

- **Cambio de contrato** (tipos/campos): actualiza `yd_analytics.schemas`, corre
  `npm run schema`, y refleja el tipo en `packages/contract/src/index.ts`. Un cambio
  incompatible sube *major* y se anota en `CHANGELOG.md`.
- **Métricas versionadas:** cambiar una definición sube su `version` (invalida caché).
- **Cobertura** del cerebro Python ≥ 60 % (CI la verifica).
- **Marca:** el violeta está reservado a terceros; no usarlo como color propio.
- **Formato:** todo número por el formateador es-EC.
