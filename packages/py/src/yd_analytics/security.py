"""
yd_analytics.security — Autorización por métrica (rol).

role='*' = contexto interno/superusuario (bypass). En producción el rol sale de
yd.auth (el baseline de la casa) y se pasa a las funciones del motor.
"""
from __future__ import annotations


def authorize(roles: list[str], role: str, what: str) -> None:
    """Lanza PermissionError si `role` no está autorizado para `roles`."""
    if role != "*" and "*" not in roles and role not in roles:
        raise PermissionError(f"Rol {role!r} no autorizado para {what}")
