# Backend (Studio) para Railway. Un Dockerfile en la raíz manda sobre Nixpacks, así
# se evita que Railway confunda el monorepo (package.json) y compile el frontend.
# Contexto de build = raíz del repo, por eso ./packages/py está disponible.
FROM python:3.11-slim

WORKDIR /app
COPY . .

# Instala el paquete de la casa + lo necesario para servir el Studio.
RUN pip install --no-cache-dir "./packages/py[api,ingest,stats,postgres]" python-multipart "uvicorn[standard]"

ENV PORT=8000
EXPOSE 8000

# app:app resuelve a examples/studio/app.py (studio.html se sirve por __file__).
CMD uvicorn app:app --app-dir examples/studio --host 0.0.0.0 --port ${PORT}
