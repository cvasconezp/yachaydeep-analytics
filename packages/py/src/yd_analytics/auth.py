"""
yd_analytics.auth — Autenticación por API key para embeber el API en producción.

El paquete no impone infraestructura: lee las llaves de una fuente que tú provees
(por defecto, la variable de entorno ``YD_API_KEYS``) y expone dependencias FastAPI
que validan la llave **en tiempo constante** y resuelven el inquilino y el rol. Así
Core, Áncora, Kullki o un suscriptor externo montan el mismo router con SU auth.

Formato de ``YD_API_KEYS``::

    "clave_secreta_1:tenantA:admin, clave_secreta_2:tenantB:viewer"

(el rol es opcional, por defecto ``admin``; el tenant por defecto ``default``).

Modo de operación:

* Si hay llaves configuradas (o ``YD_REQUIRE_AUTH=1``) el API queda **cerrado**:
  toda petición protegida exige ``X-API-Key`` o ``Authorization: Bearer <clave>``.
* Si no hay llaves ni se exige auth, el modo es **ABIERTO** (desarrollo) y se emite
  una advertencia. Nunca despliegues en producción sin llaves.

Las funciones puras (``parse_keys``, ``load_keys``, ``allowed_origins``, ``match_key``)
no dependen de FastAPI y son testeables por separado; solo ``make_auth`` importa FastAPI.
"""
from __future__ import annotations

import logging
import os
import secrets
from dataclasses import dataclass

log = logging.getLogger("yd_analytics.auth")

_TRUE = {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class ApiKey:
    """Principal resuelto a partir de una API key válida."""
    key: str
    tenant: str = "default"
    role: str = "admin"


def parse_keys(raw: str | None) -> dict[str, ApiKey]:
    """Parsea ``"clave:tenant:rol, clave2:tenant2"`` → {clave: ApiKey}."""
    keys: dict[str, ApiKey] = {}
    for chunk in (raw or "").split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = [p.strip() for p in chunk.split(":")]
        key = parts[0]
        if not key:
            continue
        tenant = parts[1] if len(parts) > 1 and parts[1] else "default"
        role = parts[2] if len(parts) > 2 and parts[2] else "admin"
        keys[key] = ApiKey(key=key, tenant=tenant, role=role)
    return keys


def load_keys() -> dict[str, ApiKey]:
    """Carga las llaves desde la variable de entorno ``YD_API_KEYS``."""
    return parse_keys(os.environ.get("YD_API_KEYS"))


def match_key(keys: dict[str, ApiKey], presented: str | None) -> ApiKey | None:
    """Compara la llave presentada contra todas en **tiempo constante**.

    Recorre todas las llaves aunque haya coincidencia temprana, para no filtrar
    información por temporización."""
    if not presented:
        return None
    found: ApiKey | None = None
    for k, meta in keys.items():
        if secrets.compare_digest(k, presented):
            found = meta
    return found


def allowed_origins(*, dev_open: bool) -> list[str]:
    """Orígenes CORS permitidos desde ``YD_ALLOWED_ORIGINS`` (lista separada por comas).

    Si no se define: en modo abierto (dev) devuelve ``["*"]`` por comodidad; con auth
    exigida devuelve ``[]`` (hay que declarar explícitamente los orígenes del cliente)."""
    raw = (os.environ.get("YD_ALLOWED_ORIGINS") or "").strip()
    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]
    return ["*"] if dev_open else []


@dataclass(frozen=True)
class Auth:
    """Paquete de dependencias FastAPI listas para inyectar."""
    get_principal: object       # Callable -> ApiKey
    get_role: object            # Callable -> str
    get_tenant: object          # Callable -> str
    require: bool               # ¿auth exigida?
    keys: dict


def make_auth(*, keys: dict[str, ApiKey] | None = None,
             require: bool | None = None) -> Auth:
    """Construye las dependencias de auth.

    * ``keys``: mapa de llaves (por defecto, de ``YD_API_KEYS``).
    * ``require``: fuerza el cierre. Por defecto ``True`` si hay llaves o
      ``YD_REQUIRE_AUTH`` está activo.
    """
    from fastapi import Depends, Header, HTTPException

    keys = load_keys() if keys is None else keys
    if require is None:
        require = bool(keys) or (os.environ.get("YD_REQUIRE_AUTH", "").lower() in _TRUE)

    if require and not keys:
        log.warning("YD_REQUIRE_AUTH activo pero YD_API_KEYS está vacío: se rechazará TODO.")
    if not require:
        log.warning("yd_analytics.auth en modo ABIERTO (sin API keys). No usar en producción.")

    def get_principal(
        authorization: str | None = Header(default=None),
        x_api_key: str | None = Header(default=None),
    ) -> ApiKey:
        presented = x_api_key
        if not presented and authorization and authorization.lower().startswith("bearer "):
            presented = authorization[7:].strip()
        if not require:
            return ApiKey(key="", tenant="default", role="admin")
        if not presented:
            raise HTTPException(
                status_code=401,
                detail="Falta API key (envía X-API-Key o Authorization: Bearer <clave>).",
            )
        meta = match_key(keys, presented)
        if meta is None:
            raise HTTPException(status_code=403, detail="API key inválida.")
        return meta

    def get_role(principal: ApiKey = Depends(get_principal)) -> str:
        return principal.role

    def get_tenant(principal: ApiKey = Depends(get_principal)) -> str:
        return principal.tenant

    return Auth(get_principal=get_principal, get_role=get_role,
                get_tenant=get_tenant, require=require, keys=keys)
