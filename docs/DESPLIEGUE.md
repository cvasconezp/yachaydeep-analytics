# DESPLIEGUE — Subir a GitHub y publicar (Railway + Vercel)

Igual que tus otras apps: **GitHub** (código) + **Railway** (backend FastAPI + Postgres)
+ **Vercel** (frontend/landing), bajo `analytics.yachaydeep.com`.

## 1. Subir a GitHub (paso a paso)

El repo ya viene con `git init` y commits. Solo falta conectarlo y empujar.

**Opción A — con GitHub CLI (`gh`):**
```bash
cd yachaydeep-analytics
gh auth login                       # una sola vez
gh repo create cvasconezp/yachaydeep-analytics --private --source=. --remote=origin --push
```

**Opción B — manual:**
1. Crea un repo vacío en github.com → `cvasconezp/yachaydeep-analytics` (sin README).
2. Conéctalo y empuja:
```bash
cd yachaydeep-analytics
git remote add origin https://github.com/cvasconezp/yachaydeep-analytics.git
git branch -M main
git push -u origin main
```

Listo: el CI (`.github/workflows/ci.yml`) corre las pruebas en cada push.

> Para cambios futuros: `git add -A && git commit -m "..." && git push`.

## 2. Backend en Railway (FastAPI + Postgres)

1. **railway.app** → *New Project* → *Deploy from GitHub repo* → elige el repo.
2. **Root Directory:** `examples/studio` (o tu propia app que monte `make_router`).
3. **Build:** `pip install -e ../../packages/py[api,ingest] && pip install python-multipart uvicorn`
   (o añade un `requirements.txt`).
4. **Start:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. **Base de datos:** *New* → *Database* → *PostgreSQL*. Railway inyecta `DATABASE_URL`.
6. **Variables:** `ANALYTICS_DB_URL=$DATABASE_URL` (y las de `yd/` cuando integres auth).
7. Railway te da una URL: será tu API (`api.analytics.yachaydeep.com` al añadir dominio).

## 3. Frontend / landing en Vercel

1. **vercel.com** → *Add New Project* → importa el repo.
2. **Root Directory:** `examples/vite-app` (o tu landing).
3. **Build:** `npm install && npm run build` · **Output:** `dist`.
4. **Env:** `VITE_ANALYTICS_API=https://<tu-api-en-railway>`
5. Deploy. Vercel te da una URL de preview.

## 4. Dominio `analytics.yachaydeep.com`

En tu DNS (donde administras `yachaydeep.com`):

| Registro | Apunta a | Para |
|---|---|---|
| `analytics` (CNAME) | Vercel | landing + app |
| `*.analytics` (CNAME, wildcard) | Vercel | subdominios por inquilino (`kullki.analytics…`) |
| `api.analytics` (CNAME) | Railway | la API |

En Vercel añade el dominio `analytics.yachaydeep.com` **y** `*.analytics.yachaydeep.com`
(para el multi-tenant por subdominio). En Railway añade `api.analytics.yachaydeep.com`.
El front resuelve el inquilino con `tenant_from_host(host)` (ver MULTI-TENANT.md).

## 5. Publicar los paquetes (opcional, para instalar en Core/Áncora/Kullki)

- **npm** (`@yachaydeep/analytics-contract`, `@yachaydeep/dashboard`):
  `npm publish --access restricted` desde cada `packages/*` (o GitHub Packages).
- **PyPI / GitHub Packages** (`yd-analytics`): `python -m build && twine upload dist/*`
  (o instala por git: `pip install "yd-analytics @ git+https://github.com/cvasconezp/yachaydeep-analytics#subdirectory=packages/py"`).

Así cada app hace `npm i @yachaydeep/dashboard` y `pip install yd-analytics` por versión.

## 6. Checklist

- [ ] `git push` a GitHub · CI verde.
- [ ] Railway: API arriba + Postgres + `DATABASE_URL`.
- [ ] Vercel: front arriba + `VITE_ANALYTICS_API`.
- [ ] DNS: `analytics`, `*.analytics`, `api.analytics`.
- [ ] Migrar tus datos a la Postgres del inquilino y registrar sus métricas.

---

*Yachay Deep · Despliegue v0.1 · Julio 2026.*
