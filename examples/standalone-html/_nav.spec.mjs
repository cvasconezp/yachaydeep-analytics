import { createRequire } from "module";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const HERE = dirname(fileURLToPath(import.meta.url));
const EXEC = process.env.CHROMIUM || "/opt/pw-browsers/chromium";
const U = (f) => "file://" + join(HERE, f);

let passed = 0, failed = 0;
const ok = (n, c) => c ? (passed++, console.log("  ✓ " + n)) : (failed++, console.error("  ✗ " + n));

const browser = await chromium.launch({ executablePath: EXEC }).catch(() => chromium.launch());
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });

async function load(f) {
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  await page.goto(U(f), { waitUntil: "domcontentloaded" });
  return errors;
}

// crossfilter = primero (sin "anterior"); report = último (sin "siguiente")
for (const [f, hasPrev, hasNext, active] of [
  ["crossfilter-demo.html", false, true, "Cross-highlighting"],
  ["builder-demo.html", true, true, "Constructor de tablero"],
  ["report-demo.html", true, false, "Informe con estadística"],
]) {
  await load(f);
  ok(`${f}: barra única`, (await page.$$("nav.ydnav")).length === 1);
  ok(`${f}: 11 accesos`, (await page.$$("nav.ydnav .strip a")).length === 11);
  const on = await page.$$eval("nav.ydnav .strip a.on", (a) => a.map((x) => x.textContent.trim()));
  ok(`${f}: demo actual marcado = «${active}»`, on.length === 1 && on[0] === active);
  ok(`${f}: enlace Volver a la galería`, await page.$('nav.ydnav a.home[href="index.html#demos"]') !== null);
  const prevA = await page.$('nav.ydnav .step a[aria-label="Demo anterior"]');
  const nextA = await page.$('nav.ydnav .step a[aria-label="Demo siguiente"]');
  ok(`${f}: «anterior» ${hasPrev ? "activo" : "deshabilitado"}`, (prevA !== null) === hasPrev);
  ok(`${f}: «siguiente» ${hasNext ? "activo" : "deshabilitado"}`, (nextA !== null) === hasNext);
  // barra pegajosa arriba
  const sticky = await page.$eval("nav.ydnav", (n) => getComputedStyle(n).position);
  ok(`${f}: barra sticky`, sticky === "sticky");
}

// El «siguiente» de crossfilter lleva a gallery-demo
await load("crossfilter-demo.html");
const nextHref = await page.$eval('nav.ydnav .step a[aria-label="Demo siguiente"]', (a) => a.getAttribute("href"));
ok("siguiente de crossfilter → gallery-demo", nextHref === "gallery-demo.html");

await browser.close();
console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
