# Ejemplo · Vite (consumo nativo)

Muestra cómo una app monta `@yachaydeep/dashboard` en **sus propias rutas** (no
embebido), con sus tokens de marca. Consume el backend del ejemplo hermano.

```bash
# 1) levanta el backend del ejemplo (carpeta ../backend-demo)
# 2) instala y corre este ejemplo (desde la raíz del monorepo, con workspaces):
npm install
npm --workspace example-vite-app run dev     # http://localhost:5173
```

Cambia `--brand-primary` en `index.html` (aquí verde) y el mismo tablero se ve con
otra marca — igual que con `@yachaydeep/brand`. Endpoint configurable con
`VITE_ANALYTICS_API`.
