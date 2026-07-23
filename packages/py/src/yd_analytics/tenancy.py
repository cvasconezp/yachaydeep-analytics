"""
yd_analytics.tenancy — Multi-tenant: aislar los datos de cada inquilino.

Pensado para el plan de la casa: primero Core, Áncora y Kullki como inquilinos
internos, y luego suscriptores externos en analytics.yachaydeep.com. El motor ya es
agnóstico del `Engine`; aquí se resuelve **qué Engine** (y rol/plan) corresponde a la
petición, por subdominio o token.

Modelos de aislamiento soportados:
- **DB-por-inquilino** (más fuerte): cada tenant, su base/DSN. Recomendado para tus
  apps y para planes de pago.
- **Row-level** (más barato, muchos suscriptores): una base compartida con columna
  `tenant_id`; `row_filter()` inyecta el filtro. La app debe aplicarlo en sus vistas.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Callable

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


@dataclass
class Tenant:
    id: str
    engine: Engine
    role: str = "admin"
    plan: str = "free"                       # free | pro | enterprise (gating de features)
    limits: dict = field(default_factory=dict)


class TenantResolver:
    """Registro de inquilinos y resolución por id/subdominio."""

    def __init__(self) -> None:
        self._tenants: dict[str, Tenant] = {}

    def register(self, tenant: Tenant) -> Tenant:
        self._tenants[tenant.id] = tenant
        return tenant

    def register_dsn(self, tenant_id: str, dsn: str, *, role: str = "admin",
                     plan: str = "free", **engine_kwargs) -> Tenant:
        eng = create_engine(dsn, **engine_kwargs)
        return self.register(Tenant(id=tenant_id, engine=eng, role=role, plan=plan))

    def get(self, tenant_id: str) -> Tenant:
        if tenant_id not in self._tenants:
            raise KeyError(f"Inquilino no registrado: {tenant_id!r}")
        return self._tenants[tenant_id]

    def engine_for(self, tenant_id: str) -> Engine:
        return self.get(tenant_id).engine

    def ids(self) -> list[str]:
        return list(self._tenants)


def tenant_from_host(host: str, base: str = "analytics.yachaydeep.com") -> str | None:
    """kullki.analytics.yachaydeep.com → 'kullki'. Devuelve None si es el dominio base."""
    host = (host or "").split(":")[0].lower().strip()
    if host == base or not host.endswith("." + base):
        return None
    sub = host[: -(len(base) + 1)]
    return sub or None


def row_filter(tenant_id: str) -> str:
    """Cláusula SQL para aislamiento row-level (base compartida con tenant_id)."""
    if not re.match(r"^[A-Za-z0-9_-]+$", tenant_id):
        raise ValueError(f"tenant_id inválido: {tenant_id!r}")
    return f"tenant_id = '{tenant_id}'"


def make_get_engine(resolver: TenantResolver,
                    tenant_of_request: Callable[..., str]) -> Callable[[], Engine]:
    """Construye el `get_engine` que espera make_router, resolviendo el inquilino de
    la petición (p. ej. del subdominio o de un claim del JWT de yd.auth)."""
    def _get_engine() -> Engine:
        return resolver.engine_for(tenant_of_request())
    return _get_engine
