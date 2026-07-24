/* @yachaydeep-yd/dashboard — Runtime del tablero.

   Lee un DashboardSpec, coloca los paneles en grilla y ofrece los slicers de los
   filtros globales + un botón de limpiar. Todo cuelga del FilterStore compartido.

   Uso en una app de casa:
     <QueryClientProvider client={qc}>
       <Dashboard spec={miDashboardSpec} />
     </QueryClientProvider>
*/
import { Panel } from "./Panel";
import { useFilters } from "./filterStore";
import type { DashboardSpec } from "./types";

export function Dashboard({ spec }: { spec: DashboardSpec }) {
  const filters = useFilters((s) => s.filters);
  const clear = useFilters((s) => s.clear);
  const activos = Object.values(filters);

  return (
    <section className="yd-dashboard">
      <header className="yd-dashboard__head">
        <h2>{spec.titulo}</h2>
        <div className="yd-dashboard__filtros">
          {activos.length > 0 ? (
            <>
              {activos.map((f) => (
                <button key={f.field} className="yd-chip" onClick={() => clear(f.field)}>
                  {f.field}: {String(f.value)} ✕
                </button>
              ))}
              <button className="yd-chip yd-chip--reset" onClick={() => clear()}>
                Limpiar todo
              </button>
            </>
          ) : (
            <span className="yd-dashboard__hint">Haz clic en una barra para filtrar todo el tablero</span>
          )}
        </div>
      </header>

      <div className="yd-grid">
        {spec.paneles.map((p) => (
          <div key={p.id} className={`yd-cell yd-cell--${p.size ?? "md"}`}>
            <Panel spec={p} />
          </div>
        ))}
      </div>
    </section>
  );
}
