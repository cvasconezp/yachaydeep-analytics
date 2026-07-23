# MULTI-TENANT — De tus apps a suscripciones

> Cómo pasar de "lo uso en Kullki, Áncora y Core" a "lo vendo por suscripción" en
> `analytics.yachaydeep.com`, aislando los datos de cada inquilino.

## 0. El plan

- **Landing:** `analytics.yachaydeep.com` (marketing, precios, "entrar").
- **App:** `analytics.yachaydeep.com/analytics` — o **un subdominio por inquilino**:
  `kullki.analytics.yachaydeep.com`, `ancora.…`, y para clientes externos
  `cliente.analytics.yachaydeep.com`.
- **Fase 1:** Core, Áncora y Kullki como **inquilinos internos**.
- **Fase 2:** suscriptores externos (planes free / pro / enterprise).

## 1. Cualquier dato, cualquier sector

El sistema **no sabe de educación** (es solo el dominio de los demos). El profiler
infiere el tipo de cada columna y el resolver elige el gráfico por la **forma del
dato**, no por el negocio. Sirve igual para **turismo** (ocupación por temporada),
**empresa** (ventas por región), **salud**, **finanzas** — cualquier dato cuantitativo
tabular. Cada inquilino trae su propio `DATA_DICTIONARY`; el motor es el mismo.

## 2. Modelos de aislamiento

| Modelo | Aislamiento | Costo/operación | Cuándo |
|---|---|---|---|
| **DB-por-inquilino** | Máximo (base separada) | Más caro | Tus apps y planes **pro/enterprise** |
| **Schema-por-inquilino** | Alto (mismo cluster) | Medio | Punto medio |
| **Row-level** (`tenant_id`) | Lógico (filtro) | Más barato | Muchos suscriptores **free**, datos poco sensibles |

Recomendación: **DB-por-inquilino** para Core/Áncora/Kullki y pago; **row-level** para
el tier gratuito masivo. El módulo `tenancy` soporta ambos.

## 3. Cómo se resuelve el inquilino (código)

```python
from yd_analytics import TenantResolver, make_get_engine, make_router, tenant_from_host

res = TenantResolver()
res.register_dsn("kullki", "postgresql://…/kullki", plan="enterprise")
res.register_dsn("ancora", "postgresql://…/ancora", plan="pro")

def tenant_of_request():                     # del subdominio (o de un claim del JWT)
    return tenant_from_host(request.headers["host"]) or "demo"

app.include_router(make_router(
    get_engine=make_get_engine(res, tenant_of_request),   # ← el Engine del inquilino
    get_role=rol_desde_yd_auth,                            # ← su rol
))
```

El `make_router` ya recibe `get_engine`/`get_role`: multi-tenant es **resolver cuál**
por petición. Cada consulta va a la base del inquilino; **los datos no se cruzan**.

## 4. Suscripciones y planes

El `Tenant` lleva `plan` y `limits`. Con eso se hace *feature gating*:

| Plan | Filas | Refresco | Conectores | Asientos | Extras |
|---|---|---|---|---|---|
| free | tope bajo, row-level | diario | CSV/Excel + 1 BD | 1–3 | marca YD |
| pro | alto, DB propia | horario | + MySQL/Sheets | equipo | marca propia |
| enterprise | ilimitado | tiempo real | todos + SSO | ilimitado | k-anon, on-prem |

La app consulta `tenant.plan` para habilitar/limitar (tamaño, cadencia, conectores).

## 5. Seguridad multi-tenant

- **Aislamiento por Engine** (o `row_filter('tenant_id')` en row-level): nadie ve
  datos de otro inquilino.
- **Rol por inquilino** vía `yd.auth`; autorización por métrica (§ seguridad).
- **PII:** índice ciego + k-anon + sin llaves en la capa de analítica (LOPDP).
- **Aislar también la caché**: la clave de caché ya incluye la métrica+filtros; en
  multi-tenant, prefijar con el `tenant_id`.

## 6. Topología de despliegue (ver DESPLIEGUE.md)

```
                analytics.yachaydeep.com            (landing + app)         → Vercel
    kullki. / ancora. / cliente.analytics.yachaydeep.com (mismo front, tenant por host)
                              │  /api  →  api.analytics.yachaydeep.com       → Railway (FastAPI)
                              ▼
        Postgres por inquilino (o compartido row-level)  → Railway/Neon/Supabase
```

## 7. Hoja de ruta

| Fase | Qué | Resultado |
|---|---|---|
| 0 | `tenancy` + DB-por-inquilino para Core/Áncora/Kullki | Multi-tenant interno funcionando |
| 1 | Subdominios + resolución por host + planes | Base para vender |
| 2 | Alta self-serve + billing (Stripe) + tier free row-level | Suscripciones |
| 3 | Conectores extra, SSO, on-prem enterprise | Escala comercial |

---

*Yachay Deep · Multi-tenant y suscripciones v0.1 · Julio 2026.*
