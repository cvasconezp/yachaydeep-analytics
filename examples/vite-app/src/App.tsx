import { useEffect, useState } from "react";
import { Dashboard, NetworkView } from "@yachaydeep/dashboard";
import type { DashboardSpec, GraphResult } from "@yachaydeep/analytics-contract";

const API = import.meta.env.VITE_ANALYTICS_API ?? "http://127.0.0.1:8000";

// Un tablero declarativo: el runtime lo pinta y resuelve el gráfico por forma.
const spec: DashboardSpec = {
  id: "core-early-warning",
  titulo: "Alerta temprana — ejemplo",
  filtrosGlobales: ["periodo", "carrera", "jornada"],
  paneles: [
    { id: "kpi", metric: "estudiantes_en_riesgo", size: "sm" },
    { id: "serie", metric: "riesgo_promedio", dimensions: ["periodo"], grain: "periodo", size: "lg" },
    { id: "porcarrera", metric: "estudiantes_en_riesgo", dimensions: ["carrera"], size: "md" },
  ],
};

export default function App() {
  const [red, setRed] = useState<GraphResult | null>(null);
  useEffect(() => {
    fetch(`${API}/analytics/graph/malla_prerrequisitos`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: "{}",
    }).then((r) => r.json()).then(setRed).catch(() => setRed(null));
  }, []);

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto" }}>
      <h2 style={{ padding: "16px 16px 0" }}>Ejemplo de consumo nativo de @yachaydeep/dashboard</h2>
      <Dashboard spec={spec} />
      <div style={{ padding: 16 }}>
        <h3>Red de prerrequisitos (forma graph · estilo VOSviewer)</h3>
        {red ? <NetworkView data={red} colorBy="cluster" height={520} /> : <p>Cargando red…</p>}
      </div>
    </div>
  );
}
