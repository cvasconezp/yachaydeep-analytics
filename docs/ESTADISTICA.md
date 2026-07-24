# ESTADÍSTICA E INFORMES

Yachay Deep Analytics no solo grafica: calcula **estadística real** sobre tus datos
(con numpy/scipy) y redacta un **informe** que resume cada gráfico. Los números
salen del cálculo; los resúmenes se arman de forma **determinista** a partir de esos
números — nunca inventados por un modelo. Pensado para exigencias de exactitud (p. ej.
análisis electoral).

## Qué calcula (`yd_analytics.stats`)

**Descriptiva.** n, media y mediana (juntas: su brecha delata la asimetría), desviación
estándar muestral (ddof=1), varianza, mín/máx/rango, suma, error estándar, IC 95 % de la
media (t de Student), cuartiles e IQR, coeficiente de variación, asimetría y curtosis,
percentiles p1…p99, y una etiqueta de forma.

**Distribución.** Prueba de normalidad (Shapiro-Wilk si n≤5000, D'Agostino-Pearson si
mayor).

**Atípicos.** Por IQR (1,5×) y por z-score (>3). Se **reportan**, no se eliminan solos.

**Tendencia y pronóstico.** Regresión lineal OLS (pendiente, R², p, error), prueba
**Mann-Kendall** (no paramétrica, robusta), cambio período-a-período, cambio total, CAGR,
y pronóstico del próximo período con banda al 95 %.

**Correlación.** Pearson y Spearman con p y R². *(Correlación ≠ causación: se advierte.)*

**Categórico / concentración.** Reparto y líder, HHI (Herfindahl) normalizado, Gini,
entropía de Shannon, y **chi-cuadrado** de bondad de ajuste (¿el reparto es uniforme?) y
de independencia con **V de Cramér**.

**Comparación de grupos.** ANOVA (paramétrica) con η² y Kruskal-Wallis (no paramétrica).

**Proporciones — clave electoral.** Estimación + **intervalo de Wilson** + **margen de
error**, con corrección por población finita; tamaño de muestra para un margen objetivo;
margen de error de una encuesta dada. Un traslape de intervalos entre dos candidatos =
**empate técnico**.

### Cautelas que emite

Muestra pequeña (n<30 → poca potencia), correlación ≠ causación, y evita la precisión
falsa (redondea y usa rangos). Para comparaciones múltiples, recuerda ajustar α
(Bonferroni).

## Cómo se usa

Motor (Python):

```python
from yd_analytics import stats
stats.describe(valores)                      # descriptiva completa
stats.trend(serie)                           # tendencia + Mann-Kendall + pronóstico
stats.proportion_ci(1360, 4000, population=13_500_000)   # intención de voto ± margen
stats.summarize_result(shape, filas, columnas)           # batería según la forma
```

HTTP (Studio):

```
POST /analytics/stats   {"metric": "...", "dimensions": ["..."]}     → estadística real
POST /report            {"titulo": "...", "panels": [{"metric": "...", ...}]}  → informe HTML
```

Si `/report` no recibe paneles, usa el último tablero propuesto tras subir un archivo.

## Informe (`yd_analytics.report`)

`build_report(paneles, titulo=…)` devuelve un **HTML autocontenido** con la marca de la
casa: resumen ejecutivo, un gráfico por panel (SVG), tarjetas de estadísticos, y el
resumen + cautelas de cada gráfico. Tipos de panel: `timeseries`, `category`,
`correlation`, `distribution`, `scalar` y `proportion` (encuesta/voto: `{k, n, population}`).

Demo: `examples/standalone-html/report-demo.html` (informe electoral de muestra).

---

*Yachay Deep · Estadística e informes v0.1 · Julio 2026.*
