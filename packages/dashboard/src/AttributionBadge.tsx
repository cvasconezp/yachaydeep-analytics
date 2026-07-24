/* @yachaydeep-yd/dashboard — AttributionBadge: firma de atribución para tableros
   embebidos. Esquina inferior derecha, cursiva, con una FRANJA de acento que realza.

   Auto-contenido (estilos en línea): se ve igual sin importar el CSS de la app
   anfitriona. Enlaza a analytics.yachaydeep.com. Se puede ocultar en planes de pago
   (prop `attribution={false}` en <Dashboard>). Variante A (píldora + franja lateral).

   Color de producto de Analytics (familia "hielo/datos", §7.3 de la marca): cian. */
import { useState, type CSSProperties } from "react";

// Color propio de Yachay Deep Analytics (propuesta de graduación).
const CYAN = "#0E9AB8";
const CYAN_DARK = "#0B7C93";
const CYAN_LIGHT = "#3FC0DA";

const THEMES = {
  light: { bg: "rgba(255,255,255,.92)", fg: "#0F2444", muted: "#6b7280", border: "rgba(15,36,68,.08)" },
  dark: { bg: "rgba(16,32,58,.72)", fg: "#eaf2fb", muted: "#9db4d6", border: "rgba(168,220,232,.22)" },
} as const;

export interface AttributionBadgeProps {
  /** Tema del contenedor donde se embebe. */
  theme?: "light" | "dark";
  /** Destino del enlace. */
  href?: string;
  /** Marca opcional (glifo/emoji) a la izquierda del texto. Hoy: emoji provisional. */
  mark?: string;
  /**
   * Color de la franja de acento. Por defecto adopta el color de la PÁGINA
   * ANFITRIONA vía la variable CSS `--yd-accent`; si esa variable no está
   * definida (uso standalone), cae al cian propio de Analytics. La app que
   * embebe puede pasar su color de marca aquí o definir `--yd-accent`.
   */
  accent?: string;
}

export function AttributionBadge({
  theme = "light",
  href = "https://analytics.yachaydeep.com",
  mark = "📊",
  accent = `var(--yd-accent, ${CYAN})`,
}: AttributionBadgeProps) {
  const [hover, setHover] = useState(false);
  const t = THEMES[theme];

  const badge: CSSProperties = {
    position: "absolute",
    right: 12,
    bottom: 12,
    display: "inline-flex",
    alignItems: "center",
    gap: 8,
    padding: "6px 12px 6px 10px",
    borderRadius: 999,
    background: t.bg,
    WebkitBackdropFilter: "blur(6px)",
    backdropFilter: "blur(6px)",
    border: `1px solid ${t.border}`,
    boxShadow: hover
      ? "0 6px 16px -4px rgba(15,36,68,.35)"
      : "0 2px 10px -2px rgba(15,36,68,.25)",
    transform: hover ? "translateY(-1px)" : "none",
    transition: "transform .15s ease, box-shadow .15s ease",
    fontFamily: '"Instrument Sans", system-ui, -apple-system, sans-serif',
    fontSize: 12,
    lineHeight: 1,
    color: t.fg,
    textDecoration: "none",
    cursor: "pointer",
    zIndex: 5,
  };
  const stripe: CSSProperties = {
    width: 4,
    height: 16,
    borderRadius: 2,
    // Franja sólida en el color del host (o cian por defecto). Sólido = compatible
    // con cualquier color, incluyendo `currentColor` o una variable CSS del host.
    background: accent,
    flex: "0 0 auto",
  };
  const wordmark: CSSProperties = { fontStyle: "italic", fontWeight: 600, letterSpacing: ".01em" };
  const sub: CSSProperties = { fontStyle: "italic", fontWeight: 500, color: t.muted };

  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      style={badge}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      aria-label="Hecho con Yachay Deep Analytics"
      data-yd-attribution
    >
      <span style={stripe} aria-hidden="true" />
      {mark && <span style={{ fontSize: 14, lineHeight: 1 }} aria-hidden="true">{mark}</span>}
      <span style={wordmark}>
        Yachay Deep <span style={sub}>Analytics</span>
      </span>
    </a>
  );
}

/** Color de producto de Analytics, exportado para reutilizar (franjas, acentos). */
export const ANALYTICS_COLOR = { base: CYAN, dark: CYAN_DARK, light: CYAN_LIGHT } as const;
