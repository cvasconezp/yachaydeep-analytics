#!/usr/bin/env python3
"""Inyecta una barra de navegación entre demos (sticky) en cada *-demo.html.
Idempotente: si ya existe la barra (marcador YDNAV), la reemplaza."""
import re, pathlib

DEMOS = [
    ("crossfilter-demo.html",   "Cross-highlighting"),
    ("gallery-demo.html",       "Galería de gráficos"),
    ("ask-demo.html",           "Pregúntale a tus datos"),
    ("ingest-demo.html",        "Sube y limpia"),
    ("model-editor-demo.html",  "Editor de relaciones"),
    ("builder-demo.html",       "Constructor de tablero"),
    ("network-demo.html",       "Grafo de redes"),
    ("graph-demo.html",         "Prerrequisitos"),
    ("dashboard-demo.html",     "Tablero interactivo"),
    ("telemetry-demo.html",     "Tablero de uso"),
    ("report-demo.html",        "Informe con estadística"),
]

CHEV_L = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" aria-hidden="true"><path d="M15 18l-6-6 6-6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
CHEV_R = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" aria-hidden="true"><path d="M9 6l6 6-6 6" stroke-linecap="round" stroke-linejoin="round"/></svg>'

STYLE = """<style id="ydnav-style">
.ydnav{position:sticky;top:0;z-index:9999;background:rgba(255,255,255,.94);-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px);border-bottom:1px solid #e4e3dc;font-family:'Spline Sans',system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.ydnav *{box-sizing:border-box}
.ydnav .in{display:flex;align-items:center;gap:10px;max-width:1160px;margin:0 auto;padding:8px 18px}
.ydnav a{text-decoration:none}
.ydnav .home{display:inline-flex;align-items:center;gap:5px;color:#0F2444;font-weight:700;font-size:13px;white-space:nowrap}
.ydnav .home svg{width:16px;height:16px;flex:0 0 auto}
.ydnav .sep{width:1px;height:22px;background:#e4e3dc;flex:0 0 auto}
.ydnav .strip{display:flex;gap:7px;overflow-x:auto;scroll-behavior:smooth;-ms-overflow-style:none;scrollbar-width:none;flex:1 1 auto;padding:2px 0}
.ydnav .strip::-webkit-scrollbar{display:none}
.ydnav .strip a{flex:0 0 auto;font-size:12.5px;line-height:1;padding:6px 11px;border-radius:999px;color:#52514e;border:1px solid #e4e3dc;background:#fff;white-space:nowrap;transition:border-color .12s,color .12s}
.ydnav .strip a:hover{border-color:#c3c2b7;color:#0F2444}
.ydnav .strip a.on{background:#0F2444;color:#fff;border-color:#0F2444;font-weight:600}
.ydnav .step{display:flex;gap:5px;flex:0 0 auto}
.ydnav .step a,.ydnav .step span{display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;border-radius:8px;border:1px solid #e4e3dc;color:#52514e;background:#fff}
.ydnav .step a svg,.ydnav .step span svg{width:16px;height:16px}
.ydnav .step span{opacity:.32;cursor:default}
.ydnav .step a:hover{border-color:#c3c2b7;color:#0F2444}
@media(max-width:620px){.ydnav .home span{display:none}.ydnav .in{gap:8px;padding:8px 12px}}
</style>"""

# Script aparte (fuera de f-strings) para no tener que escapar llaves.
NAV_JS = ('<script id="ydnav-js">(function(){var s=document.getElementById("ydstrip");'
          'if(!s)return;var on=s.querySelector("a.on");if(on){var l=on.offsetLeft-'
          's.clientWidth/2+on.clientWidth/2;s.scrollTo({left:l>0?l:0});}})();</script>')

def build_bar(current):
    idx = [d[0] for d in DEMOS].index(current)
    pills = []
    for href, label in DEMOS:
        on = " on" if href == current else ""
        aria = ' aria-current="page"' if href == current else ""
        pills.append(f'<a class="p{on}" href="{href}"{aria}>{label}</a>')
    strip = "".join(pills)
    prev = (f'<a href="{DEMOS[idx-1][0]}" title="Anterior: {DEMOS[idx-1][1]}" aria-label="Demo anterior">{CHEV_L}</a>'
            if idx > 0 else f'<span aria-hidden="true">{CHEV_L}</span>')
    nxt  = (f'<a href="{DEMOS[idx+1][0]}" title="Siguiente: {DEMOS[idx+1][1]}" aria-label="Demo siguiente">{CHEV_R}</a>'
            if idx < len(DEMOS)-1 else f'<span aria-hidden="true">{CHEV_R}</span>')
    return (
        f'<!--YDNAV-->{STYLE}'
        f'<nav class="ydnav" aria-label="Navegación entre demos">'
        f'<div class="in">'
        f'<a class="home" href="index.html#demos" title="Volver a la galería de demos">{CHEV_L}<span>Demos</span></a>'
        f'<div class="sep"></div>'
        f'<div class="strip" id="ydstrip" role="tablist">{strip}</div>'
        f'<div class="step">{prev}{nxt}</div>'
        f'</div></nav>'
        + NAV_JS +
        '<!--/YDNAV-->'
    )

# Marcadores para reemplazo idempotente
BLOCK_RE = re.compile(r'<!--YDNAV-->.*?<!--/YDNAV-->', re.DOTALL)
# Inserta tras el <body> REAL (el precedido por </head>), no el que aparece
# como cadena dentro del JS minificado de ECharts.
HEAD_BODY_RE = re.compile(r'(</head>\s*<body[^>]*>)', re.IGNORECASE)

here = pathlib.Path(__file__).parent
for href, _ in DEMOS:
    p = here / href
    html = p.read_text(encoding="utf-8")
    bar = build_bar(href)
    if "<!--YDNAV-->" in html:
        html = BLOCK_RE.sub(bar, html, count=1)
        action = "reemplazada"
    else:
        new, n = HEAD_BODY_RE.subn(lambda m: m.group(1) + bar, html, count=1)
        if n == 0:
            print(f"  !! {href}: no se encontró </head><body> — SIN CAMBIOS")
            continue
        html = new
        action = "insertada"
    p.write_text(html, encoding="utf-8")
    print(f"  ✓ {href}: barra {action}")

print("Listo.")
