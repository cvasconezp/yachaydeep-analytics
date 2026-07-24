/**
 * Prueba del landing (Playwright, sin framework): verifica Scrollspy, el acordeón
 * técnico único, el carrusel de demos, el favicon y que no haya errores de consola.
 *
 * Ejecutar:  node landing.spec.mjs        (desde examples/standalone-html/)
 * Requiere:  npm i -D playwright  (o el chromium del entorno)
 */
import { createRequire } from "module";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
const require = createRequire(import.meta.url);
const { chromium } = require("playwright");   // resuelve la instalación global

const HERE = dirname(fileURLToPath(import.meta.url));
const URL = "file://" + join(HERE, "index.html");
const EXEC = process.env.CHROMIUM || "/opt/pw-browsers/chromium";

let passed = 0, failed = 0;
function ok(name, cond) { cond ? (passed++, console.log("  ✓ " + name)) : (failed++, console.error("  ✗ " + name)); }

const browser = await chromium.launch({ executablePath: EXEC }).catch(() => chromium.launch());

// --- Desktop ---
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));
page.on("console", (m) => {
  // Solo errores de JS; se ignoran fallos de red de recursos (p. ej. la fuente
  // de Google no carga en un sandbox sin red — no es un bug del landing).
  if (m.type() === "error" && !/Failed to load resource|net::ERR_/i.test(m.text())) errors.push(m.text());
});
await page.goto(URL, { waitUntil: "networkidle" }).catch(() => page.goto(URL, { waitUntil: "domcontentloaded" }));

ok("sin errores de JS", errors.length === 0);
ok("favicon presente", await page.$('link[rel="icon"]') !== null);

// Acordeón técnico: UNO solo, cerrado por defecto, con 6 subtemas
ok("acordeón técnico único", (await page.$$("#tecnico details.item")).length === 1);
ok("acordeón cerrado por defecto", (await page.$$("#tecnico details.item[open]")).length === 0);
ok("6 subtemas dentro del acordeón", (await page.$$("#tecnico .tsub")).length === 6);

// Scrollspy: cada sección resalta su enlace
await page.evaluate(() => (document.documentElement.style.scrollBehavior = "auto"));
for (const [id, label] of [["como", "Cómo funciona"], ["capacidades", "Capacidades"],
  ["modos", "Modos"], ["tecnico", "Técnico"], ["demos", "Demos"]]) {
  await page.evaluate((id) => { window.scrollTo(0, document.getElementById(id).offsetTop + 90); window.dispatchEvent(new Event("scroll")); }, id);
  await page.waitForTimeout(90);
  const active = await page.evaluate(() => { const a = document.querySelector(".nav-links a.active"); return a ? a.textContent.trim() : null; });
  ok(`scrollspy resalta «${label}»`, active === label);
}

// Carrusel de demos: existe, avanza y deshabilita el prev al inicio
ok("carrusel de demos presente", await page.$("#demoCar") !== null);
ok(">= 10 demos", (await page.$$("#demoCar .demo")).length >= 10);
await page.evaluate(() => document.getElementById("demoCar").scrollTo(0, 0));
await page.waitForTimeout(60);
const prevDisabledAtStart = await page.evaluate(() => document.querySelector('.car-btn[data-dir="-1"]').disabled);
ok("botón anterior deshabilitado al inicio", prevDisabledAtStart === true);
const before = await page.evaluate(() => document.getElementById("demoCar").scrollLeft);
await page.click('.car-btn[data-dir="1"]');
await page.waitForTimeout(450);
const after = await page.evaluate(() => document.getElementById("demoCar").scrollLeft);
ok("botón siguiente desplaza el carrusel", after > before);

// --- Móvil: barra de secciones (spy-bar) visible ---
const m = await browser.newPage({ viewport: { width: 390, height: 780 } });
await m.goto(URL, { waitUntil: "networkidle" });
const spyVisible = await m.evaluate(() => getComputedStyle(document.querySelector(".spy-bar")).display !== "none");
ok("barra de secciones visible en móvil", spyVisible === true);

await browser.close();
console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
