"""
yd_analytics.telemetry — Analítica de PRODUCTO (uso de las apps de la casa).

Además de analizar los datos que el usuario carga, Yachay Deep Analytics mide el
USO de las propias apps (Core, Áncora, Kullki y otras): cuántos entran, a qué
pantallas/espacios van y desde qué dispositivo. Los eventos aterrizan en la tabla
`eventos_uso` y el MISMO motor los perfila en un tablero de uso — la app se
analiza a sí misma, sin una herramienta aparte.

Privacidad (LOPDP): NO se guarda PII. `usuario_id` debe llegar ya seudonimizado
(hash/anon-id) desde la app; nunca cédula, correo ni nombre. Las métricas que
cuentan personas usan supresión k-anónima para no re-identificar grupos diminutos.

Flujo:
    from yd_analytics import telemetry
    telemetry.ensure_events_table(engine)          # una vez
    telemetry.record_events(engine, [Event(...)])   # ingesta (endpoint /telemetry/collect)
    telemetry.register_telemetry()                  # publica las métricas de uso
    # luego se consultan con run_query() como cualquier métrica.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Iterable

from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.engine import Engine

from . import registry
from .schemas import MetricSpec

EVENTS_TABLE = "eventos_uso"

# Dimensiones permitidas para desglosar el uso (whitelist de grano).
GRANO = ["producto", "pantalla", "dispositivo", "os", "pais", "dia"]


# --- Evento de uso ---------------------------------------------------------- #

class Event(BaseModel):
    """Un evento de uso emitido por una app de la casa."""
    producto: str                       # "core" | "ancora" | "kullki" | ...
    evento: str = "pageview"            # pageview | click | accion | ...
    pantalla: str = "/"                 # ruta o "espacio" visitado
    usuario_id: str = "anon"           # SEUDÓNIMO (hash). Nunca PII.
    sesion_id: str = ""
    dispositivo: str = "desktop"       # desktop | mobile | tablet
    os: str = "otro"
    pais: str = "EC"
    ts: datetime | None = None          # UTC; si falta, se sella al registrar
    props: dict[str, Any] = Field(default_factory=dict)


# --- Esquema físico (portátil sqlite / postgres) ---------------------------- #

def _id_col(engine: Engine) -> str:
    return "id BIGSERIAL PRIMARY KEY" if engine.dialect.name == "postgresql" \
        else "id INTEGER PRIMARY KEY AUTOINCREMENT"


def ensure_events_table(engine: Engine) -> None:
    """Crea `eventos_uso` si no existe (idempotente)."""
    ddl = f"""CREATE TABLE IF NOT EXISTS {EVENTS_TABLE}(
      {_id_col(engine)},
      tenant TEXT NOT NULL DEFAULT 'default',
      producto TEXT NOT NULL,
      evento TEXT NOT NULL,
      pantalla TEXT NOT NULL,
      usuario_id TEXT NOT NULL,
      sesion_id TEXT,
      dispositivo TEXT,
      os TEXT,
      pais TEXT,
      dia TEXT NOT NULL,
      ts TEXT NOT NULL
    )"""
    with engine.begin() as c:
        c.execute(text(ddl))


def _now() -> datetime:
    return datetime.now(timezone.utc)


def record_events(engine: Engine, events: Iterable[Event | dict],
                  *, tenant: str = "default") -> int:
    """Inserta una tanda de eventos. Devuelve cuántos escribió.

    Sella `ts` (si falta) y deriva `dia` (YYYY-MM-DD) para las series temporales
    sin depender de funciones de fecha del motor."""
    rows: list[dict[str, Any]] = []
    for e in events:
        ev = e if isinstance(e, Event) else Event(**e)
        ts = ev.ts or _now()
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        rows.append({
            "tenant": tenant, "producto": ev.producto, "evento": ev.evento,
            "pantalla": ev.pantalla, "usuario_id": ev.usuario_id,
            "sesion_id": ev.sesion_id, "dispositivo": ev.dispositivo,
            "os": ev.os, "pais": ev.pais,
            "dia": ts.date().isoformat(), "ts": ts.isoformat(),
        })
    if not rows:
        return 0
    with engine.begin() as c:
        c.execute(text(f"""INSERT INTO {EVENTS_TABLE}
            (tenant,producto,evento,pantalla,usuario_id,sesion_id,dispositivo,os,pais,dia,ts)
            VALUES (:tenant,:producto,:evento,:pantalla,:usuario_id,:sesion_id,:dispositivo,:os,:pais,:dia,:ts)"""),
            rows)
    return len(rows)


# --- Métricas de uso (mismo contrato MetricSpec) ---------------------------- #

def telemetry_metrics() -> list[MetricSpec]:
    """Catálogo de métricas de uso, listas para run_query()."""
    base = dict(fuente=EVENTS_TABLE, grano=GRANO, dim_temporal="dia", version="v1")
    return [
        MetricSpec(id="uso_usuarios_activos", clase="impacto",
                   titulo="Usuarios activos", descripcion="Personas distintas que usaron la app (DAU/WAU según el rango).",
                   shape="scalar", unidad="conteo", formato="number",
                   medida={"sql": "COUNT(DISTINCT usuario_id)"}, k_anon=5, **base),
        MetricSpec(id="uso_sesiones", clase="impacto",
                   titulo="Sesiones", descripcion="Sesiones iniciadas en el periodo.",
                   shape="scalar", unidad="conteo", formato="number",
                   medida={"sql": "COUNT(DISTINCT sesion_id)"}, **base),
        MetricSpec(id="uso_eventos", clase="uso",
                   titulo="Eventos", descripcion="Total de eventos (vistas, clics, acciones).",
                   shape="scalar", unidad="conteo", formato="number",
                   medida={"sql": "COUNT(*)"}, **base),
        MetricSpec(id="uso_usuarios_por_dia", clase="impacto",
                   titulo="Usuarios activos por día", descripcion="Serie DAU.",
                   shape="scalar", unidad="conteo", formato="number",
                   medida={"sql": "COUNT(DISTINCT usuario_id)"}, k_anon=5, **base),
        MetricSpec(id="uso_top_pantallas", clase="uso",
                   titulo="Pantallas más visitadas", descripcion="A qué espacios van los usuarios.",
                   shape="scalar", unidad="conteo", formato="number",
                   medida={"sql": "COUNT(*)"}, **base),
        MetricSpec(id="uso_por_dispositivo", clase="uso",
                   titulo="Usuarios por dispositivo", descripcion="Desde qué dispositivo se conectan.",
                   shape="scalar", unidad="conteo", formato="number",
                   medida={"sql": "COUNT(DISTINCT usuario_id)"}, k_anon=5, **base),
        MetricSpec(id="uso_por_producto", clase="impacto",
                   titulo="Usuarios por producto", descripcion="Reparto de uso entre Core, Áncora, Kullki, etc.",
                   shape="scalar", unidad="conteo", formato="number",
                   medida={"sql": "COUNT(DISTINCT usuario_id)"}, k_anon=5, **base),
    ]


def register_telemetry() -> list[str]:
    """Publica las métricas de uso en el registro. Devuelve los ids registrados."""
    ids = []
    for spec in telemetry_metrics():
        registry.register(spec)
        ids.append(spec.id)
    return ids
