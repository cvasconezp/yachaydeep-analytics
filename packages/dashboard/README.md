# @yachaydeep-yd/dashboard

La **cara** del sistema de analítica de la casa: componentes React que consumen el
contrato (`@yachaydeep-yd/analytics-contract`) y pintan con ECharts. Se monta *dentro*
de cada app (Core, Áncora, Kullki), con su marca y su sesión — nunca embebido.

```tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Dashboard, NetworkView } from "@yachaydeep-yd/dashboard";

const qc = new QueryClient();

export default function AnaliticaPage({ spec, red }) {
  return (
    <QueryClientProvider client={qc}>
      <Dashboard spec={spec} />
      {/* forma graph — red con clúster/overlay */}
      <NetworkView data={red} colorBy="cluster" />
    </QueryClientProvider>
  );
}
```

**Peer deps:** `react`, `echarts`, `echarts-for-react`, `zustand`,
`@tanstack/react-query`. El endpoint se configura con `VITE_ANALYTICS_API`.

Componentes: `Dashboard` (runtime con cross-filtering + estado en URL), `Panel`
(KPI/gráfico), `NetworkView` (redes, modos *cluster* y *overlay*),
más los hooks `useMetric` / `useFilters` y el formateador es-EC.
