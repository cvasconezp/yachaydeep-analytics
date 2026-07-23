# Studio — sube tus datos y obtén un tablero

Modo **autoservicio**: una app que ata todo el sistema. Sube un Excel/CSV (o conecta
tu Postgres) y obtén un tablero automáticamente — sin código ni DAX. Sirve para
**cualquier dato cuantitativo de cualquier sector** (educación, turismo, empresa,
salud…): el sistema infiere la forma del dato, no el negocio.

```bash
pip install -e ../../packages/py[api,ingest] python-multipart uvicorn
uvicorn app:app --reload            # http://127.0.0.1:8000
```

Abre la página, sube `ejemplo.csv` (o el tuyo) y pulsa **Analizar**. El backend:
1. `ingest` → limpia y normaliza el archivo.
2. `profile` → infiere el esquema y **propone un tablero**.
3. registra las métricas y cada panel consulta `/analytics/query`.

Endpoints: `POST /ingest` (subir archivo), `POST /analytics/query`, `/assist`, `/graph`.
Para desplegar (Railway) hay `Procfile` y `requirements.txt`. Ver `docs/DESPLIEGUE.md`.

> Los mismos componentes viven **dentro** de tus apps (Core/Áncora/Kullki) con su marca.
> Para multi-tenant (varios inquilinos, suscripciones) ver `docs/MULTI-TENANT.md`.
