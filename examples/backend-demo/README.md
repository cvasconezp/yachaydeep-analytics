# Ejemplo · backend

App FastAPI mínima que **consume** `yd-analytics` como paquete (no lo reimplementa).

```bash
pip install -e ../../packages/py[api]
python seed_demo.py && python seed_graph.py
uvicorn app:app --reload      # http://127.0.0.1:8000/docs
```

Prueba:

```bash
curl -s http://127.0.0.1:8000/analytics/query -H 'Content-Type: application/json' \
  -d '{"metric":"estudiantes_en_riesgo","dimensions":["carrera"],"params":{"umbral":0.7}}'
```
