/*!
 * yd-telemetry.js — cliente de telemetría de producto de Yachay Deep Analytics.
 *
 * Mide el USO de una app de la casa (Core, Áncora, Kullki, …): vistas de pantalla,
 * dispositivo y sesión. Envía eventos por lotes a /telemetry/collect, que el mismo
 * motor perfila en un tablero de uso.
 *
 * Privacidad: NO envíes PII. `usuario_id` debe ser un seudónimo (hash/anon-id).
 * Por defecto genera un anon-id aleatorio en el navegador; si tienes el usuario
 * logueado, pásale su hash (nunca cédula/correo/nombre).
 *
 * Uso mínimo (una línea en tu app):
 *   <script src="/yd-telemetry.js"
 *           data-endpoint="https://yachay-deep-analytics-production.up.railway.app/telemetry/collect"
 *           data-producto="core"></script>
 *
 * O por API:
 *   ydTelemetry.init({ endpoint, producto: "kullki", usuarioId: hashDelUsuario });
 *   ydTelemetry.track("click", { boton: "exportar" });
 */
(function (global) {
  "use strict";

  var cfg = { endpoint: "", producto: "app", tenant: "default", usuarioId: null, auto: true, flushMs: 4000 };
  var queue = [];
  var timer = null;

  // ---- identidad seudónima (sin PII) ----
  function rid() {
    try { return (crypto.randomUUID && crypto.randomUUID()) || String(Math.random()).slice(2); }
    catch (e) { return "a" + Date.now() + String(Math.random()).slice(2); }
  }
  function anonId() {
    try {
      var k = "yd_anon";
      var v = localStorage.getItem(k);
      if (!v) { v = "anon-" + rid(); localStorage.setItem(k, v); }
      return v;
    } catch (e) { return "anon-" + rid(); }
  }
  function sessionId() {
    try {
      var k = "yd_sesion";
      var v = sessionStorage.getItem(k);
      if (!v) { v = "s-" + rid(); sessionStorage.setItem(k, v); }
      return v;
    } catch (e) { return "s-" + rid(); }
  }

  // ---- contexto (dispositivo / os) ----
  function device() {
    var ua = navigator.userAgent || "";
    if (/iPad|Tablet|PlayBook|Silk/i.test(ua) || (/Android/.test(ua) && !/Mobile/.test(ua))) return "tablet";
    if (/Mobi|Android|iPhone|iPod|Windows Phone/i.test(ua)) return "mobile";
    return "desktop";
  }
  function osName() {
    var ua = navigator.userAgent || "";
    if (/Windows/i.test(ua)) return "windows";
    if (/Android/i.test(ua)) return "android";
    if (/iPhone|iPad|iOS/i.test(ua)) return "ios";
    if (/Mac OS X/i.test(ua)) return "macos";
    if (/Linux/i.test(ua)) return "linux";
    return "otro";
  }

  function enqueue(evento, pantalla, props) {
    queue.push({
      producto: cfg.producto,
      evento: evento,
      pantalla: pantalla || (location.pathname + (location.hash || "")),
      usuario_id: cfg.usuarioId || anonId(),
      sesion_id: sessionId(),
      dispositivo: device(),
      os: osName(),
      pais: (navigator.language || "es-EC").split("-")[1] || "EC",
      props: props || {}
    });
    schedule();
  }

  function schedule() {
    if (timer) return;
    timer = setTimeout(flush, cfg.flushMs);
  }

  function flush(useBeacon) {
    if (timer) { clearTimeout(timer); timer = null; }
    if (!queue.length || !cfg.endpoint) return;
    var body = JSON.stringify({ tenant: cfg.tenant, events: queue });
    queue = [];
    try {
      if (useBeacon && navigator.sendBeacon) {
        navigator.sendBeacon(cfg.endpoint, new Blob([body], { type: "application/json" }));
      } else {
        fetch(cfg.endpoint, { method: "POST", headers: { "Content-Type": "application/json" }, body: body, keepalive: true })
          .catch(function () {});
      }
    } catch (e) { /* nunca romper la app anfitriona por telemetría */ }
  }

  // ---- API pública ----
  var api = {
    init: function (opts) {
      for (var k in (opts || {})) cfg[k] = opts[k];
      if (cfg.auto) {
        enqueue("pageview");
        // SPA: re-emite pageview al cambiar de ruta
        var _ps = history.pushState;
        history.pushState = function () { _ps.apply(this, arguments); enqueue("pageview"); };
        global.addEventListener("popstate", function () { enqueue("pageview"); });
        global.addEventListener("hashchange", function () { enqueue("pageview"); });
      }
      global.addEventListener("visibilitychange", function () {
        if (document.visibilityState === "hidden") flush(true);
      });
      global.addEventListener("pagehide", function () { flush(true); });
      return api;
    },
    track: function (evento, props) { enqueue(evento, null, props); return api; },
    pageview: function (pantalla, props) { enqueue("pageview", pantalla, props); return api; },
    flush: function () { flush(false); return api; }
  };
  global.ydTelemetry = api;

  // auto-init si se cargó con atributos data-*
  try {
    var s = document.currentScript;
    if (s && s.getAttribute("data-endpoint")) {
      api.init({
        endpoint: s.getAttribute("data-endpoint"),
        producto: s.getAttribute("data-producto") || "app",
        tenant: s.getAttribute("data-tenant") || "default",
        usuarioId: s.getAttribute("data-usuario") || null
      });
    }
  } catch (e) {}
})(typeof window !== "undefined" ? window : this);
