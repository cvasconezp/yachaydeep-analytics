"""
yd_analytics.stats — Estadística REAL (descriptiva + inferencial).

Calcula estadísticos exactos sobre los datos con numpy/scipy — no estimaciones ni
texto inventado. Sigue la metodología de análisis riguroso:

  • Centro: media y mediana juntas (su brecha delata la asimetría).
  • Dispersión: desviación estándar (muestral, ddof=1), IQR, CV, rango, SEM.
  • Percentiles: p1/p5/p10/p25/p50/p75/p90/p95/p99.
  • Forma: asimetría (skew), curtosis, prueba de normalidad (Shapiro/D'Agostino).
  • Atípicos: IQR (1.5×) y z-score (>3) — se reportan, no se eliminan solos.
  • Tendencia: regresión lineal (OLS) con R² y p, y Mann-Kendall (no paramétrico,
    robusto a valores extremos). Cambio período-a-período, CAGR, pronóstico con banda.
  • Correlación: Pearson y Spearman con p (correlación ≠ causación).
  • Categórico: reparto, concentración (HHI, Gini, entropía), chi-cuadrado de bondad
    de ajuste, y de independencia con V de Cramér.
  • Comparación de grupos: ANOVA (paramétrica) + η², Kruskal-Wallis (no paramétrica).
  • Proporciones (clave electoral): estimación + intervalo de Wilson + MARGEN DE ERROR,
    tamaño de muestra para un margen dado, con corrección por población finita.

Todas las salidas son floats/dicts JSON-serializables. Las advertencias de cautela
(muestra chica, comparaciones múltiples, precisión falsa) se emiten como banderas.
"""
from __future__ import annotations

import math
from typing import Any, Sequence

import numpy as np
from scipy import stats as _st

Number = float | int


# --------------------------------------------------------------------------- #
#  Utilidades
# --------------------------------------------------------------------------- #

def _clean(values: Sequence[Any]) -> np.ndarray:
    """Array de floats finitos; descarta None/NaN/inf."""
    out = []
    for v in values:
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if math.isfinite(f):
            out.append(f)
    return np.asarray(out, dtype=float)


def _f(x: Any) -> float | None:
    """Float seguro (None si NaN/inf/no numérico)."""
    try:
        f = float(x)
        return f if math.isfinite(f) else None
    except (TypeError, ValueError):
        return None


def z_crit(conf: float = 0.95) -> float:
    return float(_st.norm.ppf(1 - (1 - conf) / 2))


# --------------------------------------------------------------------------- #
#  Descriptiva
# --------------------------------------------------------------------------- #

def describe(values: Sequence[Any], *, conf: float = 0.95) -> dict:
    """Estadística descriptiva completa de una serie numérica."""
    x = _clean(values)
    n = int(x.size)
    if n == 0:
        return {"n": 0}
    mean = float(np.mean(x))
    median = float(np.median(x))
    std = float(np.std(x, ddof=1)) if n > 1 else 0.0
    sem = std / math.sqrt(n) if n > 1 else 0.0
    pcts = {f"p{p}": float(np.percentile(x, p)) for p in (1, 5, 10, 25, 50, 75, 90, 95, 99)}
    q1, q3 = pcts["p25"], pcts["p75"]
    iqr = q3 - q1
    # Asimetría/curtosis solo si hay varianza real (evita "precision loss" y ruido).
    has_var = std > 1e-12 and float(np.ptp(x)) > 0
    skew = float(_st.skew(x)) if (n > 2 and has_var) else 0.0
    kurt = float(_st.kurtosis(x)) if (n > 3 and has_var) else 0.0  # exceso (0 = normal)
    # IC de la media (t de Student).
    if n > 1:
        t = float(_st.t.ppf(1 - (1 - conf) / 2, df=n - 1))
        ci = (mean - t * sem, mean + t * sem)
    else:
        ci = (mean, mean)
    # Forma cualitativa.
    if abs(skew) < 0.5:
        shape = "aproximadamente simétrica"
    elif skew >= 0.5:
        shape = "asimétrica a la derecha (cola alta)"
    else:
        shape = "asimétrica a la izquierda (cola baja)"
    return {
        "n": n, "media": mean, "mediana": median, "std": std, "sem": sem,
        "var": float(np.var(x, ddof=1)) if n > 1 else 0.0,
        "min": float(np.min(x)), "max": float(np.max(x)),
        "rango": float(np.max(x) - np.min(x)),
        "suma": float(np.sum(x)),
        "q1": q1, "q3": q3, "iqr": iqr,
        "cv": (std / mean) if mean not in (0, 0.0) else None,   # coef. de variación
        "asimetria": skew, "curtosis": kurt, "forma": shape,
        "ic95_media": [ci[0], ci[1]], "conf": conf,
        "percentiles": pcts,
        "brecha_media_mediana": mean - median,
    }


def normality(values: Sequence[Any]) -> dict:
    """Prueba de normalidad: Shapiro-Wilk (n≤5000) o D'Agostino-Pearson."""
    x = _clean(values)
    n = int(x.size)
    if n < 8:
        return {"n": n, "prueba": None, "motivo": "n<8: prueba no confiable"}
    try:
        if n <= 5000:
            stat, p = _st.shapiro(x)
            prueba = "Shapiro-Wilk"
        else:
            stat, p = _st.normaltest(x)
            prueba = "D'Agostino-Pearson"
    except Exception as e:  # pragma: no cover
        return {"n": n, "prueba": None, "motivo": str(e)}
    return {"n": n, "prueba": prueba, "estadistico": float(stat),
            "p": float(p), "es_normal": bool(p >= 0.05)}


def outliers(values: Sequence[Any]) -> dict:
    """Atípicos por IQR (1.5×) y por z-score (>3). No se eliminan; se reportan."""
    x = _clean(values)
    n = int(x.size)
    if n < 4:
        return {"n": n, "iqr": {"n": 0}, "zscore": {"n": 0}}
    q1, q3 = np.percentile(x, 25), np.percentile(x, 75)
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    iqr_mask = (x < lo) | (x > hi)
    mean, std = np.mean(x), np.std(x, ddof=1)
    z = (x - mean) / std if std > 0 else np.zeros_like(x)
    z_mask = np.abs(z) > 3
    return {
        "n": n,
        "iqr": {"n": int(iqr_mask.sum()), "pct": float(iqr_mask.mean() * 100),
                "limite_inf": float(lo), "limite_sup": float(hi),
                "valores": [float(v) for v in x[iqr_mask][:20]]},
        "zscore": {"n": int(z_mask.sum()), "pct": float(z_mask.mean() * 100),
                   "umbral": 3.0, "valores": [float(v) for v in x[z_mask][:20]]},
    }


# --------------------------------------------------------------------------- #
#  Tendencia y pronóstico (series temporales)
# --------------------------------------------------------------------------- #

def mann_kendall(values: Sequence[Any]) -> dict:
    """Prueba de tendencia monótona Mann-Kendall (no paramétrica, con corrección de empates)."""
    x = _clean(values)
    n = int(x.size)
    if n < 4:
        return {"n": n, "tendencia": "indeterminada", "p": None}
    s = 0
    for i in range(n - 1):
        s += int(np.sum(np.sign(x[i + 1:] - x[i])))
    # Varianza con corrección por empates.
    unique, counts = np.unique(x, return_counts=True)
    tie = np.sum(counts * (counts - 1) * (2 * counts + 5))
    var_s = (n * (n - 1) * (2 * n + 5) - tie) / 18.0
    if var_s <= 0:
        return {"n": n, "S": int(s), "tendencia": "sin variación", "p": None}
    if s > 0:
        z = (s - 1) / math.sqrt(var_s)
    elif s < 0:
        z = (s + 1) / math.sqrt(var_s)
    else:
        z = 0.0
    p = float(2 * (1 - _st.norm.cdf(abs(z))))
    tau = float(s / (0.5 * n * (n - 1)))
    if p < 0.05:
        direccion = "creciente" if s > 0 else "decreciente"
    else:
        direccion = "sin tendencia significativa"
    return {"n": n, "S": int(s), "tau": tau, "z": float(z), "p": p, "tendencia": direccion}


def trend(values: Sequence[Any], *, labels: Sequence[Any] | None = None,
          conf: float = 0.95) -> dict:
    """Regresión lineal OLS + cambio período-a-período + CAGR + pronóstico con banda."""
    y = _clean(values)
    n = int(y.size)
    if n < 3:
        return {"n": n, "motivo": "n<3: tendencia no confiable"}
    idx = np.arange(n, dtype=float)
    lr = _st.linregress(idx, y)
    resid = y - (lr.slope * idx + lr.intercept)
    resid_std = float(np.std(resid, ddof=2)) if n > 2 else 0.0
    z = z_crit(conf)
    # Pronóstico del siguiente punto (extrapolación lineal ± banda de residuos).
    y_next = float(lr.slope * n + lr.intercept)
    band = z * resid_std
    first, last = float(y[0]), float(y[-1])
    pct_total = ((last - first) / abs(first) * 100) if first != 0 else None
    # Cambio del último período.
    pop_abs = float(y[-1] - y[-2])
    pop_pct = (pop_abs / abs(y[-2]) * 100) if y[-2] != 0 else None
    # CAGR (si todo positivo).
    cagr = None
    if first > 0 and last > 0 and n > 1:
        cagr = float((last / first) ** (1 / (n - 1)) - 1) * 100
    mk = mann_kendall(y)
    slope = float(lr.slope)
    if lr.pvalue < 0.05:
        direccion = "creciente" if slope > 0 else "decreciente"
    else:
        direccion = "estable / sin tendencia significativa"
    return {
        "n": n,
        "pendiente": slope, "intercepto": float(lr.intercept),
        "r": float(lr.rvalue), "r2": float(lr.rvalue ** 2), "p": float(lr.pvalue),
        "err_pendiente": float(lr.stderr),
        "direccion": direccion,
        "cambio_total_pct": pct_total,
        "cambio_ultimo_abs": pop_abs, "cambio_ultimo_pct": pop_pct,
        "cagr_pct": cagr,
        "pronostico_siguiente": y_next,
        "pronostico_rango": [y_next - band, y_next + band], "conf": conf,
        "mann_kendall": mk,
        "primero": first, "ultimo": last,
        "labels": list(labels) if labels is not None else None,
    }


# --------------------------------------------------------------------------- #
#  Correlación
# --------------------------------------------------------------------------- #

def correlation(x: Sequence[Any], y: Sequence[Any]) -> dict:
    """Pearson y Spearman con p. Recuerda: correlación ≠ causación."""
    xa, ya = np.asarray(_clean_pair(x, y))
    n = int(xa.size)
    if n < 3:
        return {"n": n, "motivo": "n<3: correlación no confiable"}
    pr, pp = _st.pearsonr(xa, ya)
    sr, sp = _st.spearmanr(xa, ya)

    def fuerza(r):
        a = abs(r)
        return ("muy fuerte" if a >= .8 else "fuerte" if a >= .6 else
                "moderada" if a >= .4 else "débil" if a >= .2 else "muy débil/nula")
    return {
        "n": n,
        "pearson_r": float(pr), "pearson_p": float(pp), "pearson_r2": float(pr ** 2),
        "spearman_rho": float(sr), "spearman_p": float(sp),
        "fuerza": fuerza(pr),
        "significativa": bool(pp < 0.05),
        "direccion": "positiva" if pr > 0 else "negativa" if pr < 0 else "nula",
    }


def _clean_pair(x, y):
    xs, ys = [], []
    for a, b in zip(x, y):
        fa, fb = _f(a), _f(b)
        if fa is not None and fb is not None:
            xs.append(fa); ys.append(fb)
    return np.asarray(xs), np.asarray(ys)


# --------------------------------------------------------------------------- #
#  Categórico / concentración
# --------------------------------------------------------------------------- #

def categorical_summary(labels: Sequence[Any], counts: Sequence[Any]) -> dict:
    """Reparto, top, y concentración (HHI, Gini, entropía) + chi² de uniformidad."""
    c = _clean(counts)
    labs = [str(l) for l, v in zip(labels, counts) if _f(v) is not None]
    total = float(np.sum(c))
    k = int(c.size)
    if k == 0 or total <= 0:
        return {"k": 0, "total": 0}
    shares = c / total
    order = np.argsort(-c)
    top = [{"label": labs[i], "conteo": float(c[i]), "share_pct": float(shares[i] * 100)}
           for i in order[:10]]
    hhi = float(np.sum(shares ** 2))                       # Herfindahl (0..1)
    hhi_norm = float((hhi - 1 / k) / (1 - 1 / k)) if k > 1 else 1.0
    # Gini de concentración.
    cs = np.sort(c)
    cum = np.cumsum(cs)
    gini = float((k + 1 - 2 * np.sum(cum) / cum[-1]) / k) if cum[-1] > 0 else 0.0
    # Entropía de Shannon normalizada (0 concentrado .. 1 uniforme).
    nz = shares[shares > 0]
    entropy = float(-np.sum(nz * np.log(nz)) / math.log(k)) if k > 1 else 0.0
    # Chi² de bondad de ajuste vs. uniforme.
    chi = None
    if k > 1 and total >= k:
        exp = np.full(k, total / k)
        cs2, p = _st.chisquare(c, exp)
        chi = {"chi2": float(cs2), "dof": k - 1, "p": float(p),
               "uniforme": bool(p >= 0.05)}
    conc = ("muy concentrado" if hhi_norm >= .5 else "concentrado" if hhi_norm >= .25
            else "moderado" if hhi_norm >= .1 else "repartido")
    return {"k": k, "total": total, "top": top, "hhi": hhi, "hhi_norm": hhi_norm,
            "gini": gini, "entropia": entropy, "concentracion": conc,
            "chi2_uniformidad": chi,
            "lider": top[0] if top else None}


def chi_square_independence(table: Sequence[Sequence[Number]]) -> dict:
    """Chi² de independencia entre dos variables categóricas + V de Cramér."""
    arr = np.asarray(table, dtype=float)
    if arr.ndim != 2 or arr.size == 0:
        return {"motivo": "tabla de contingencia inválida"}
    chi2, p, dof, exp = _st.chi2_contingency(arr)
    n = arr.sum()
    r, c = arr.shape
    cramer = float(math.sqrt(chi2 / (n * (min(r, c) - 1)))) if min(r, c) > 1 and n > 0 else 0.0
    return {"chi2": float(chi2), "dof": int(dof), "p": float(p),
            "cramers_v": cramer, "asociacion_significativa": bool(p < 0.05),
            "min_esperado": float(exp.min())}


# --------------------------------------------------------------------------- #
#  Comparación de grupos
# --------------------------------------------------------------------------- #

def compare_groups(groups: dict[str, Sequence[Any]]) -> dict:
    """ANOVA (paramétrica) + η² y Kruskal-Wallis (no paramétrica) entre ≥2 grupos."""
    arrs = {k: _clean(v) for k, v in groups.items()}
    arrs = {k: v for k, v in arrs.items() if v.size >= 2}
    if len(arrs) < 2:
        return {"motivo": "se requieren ≥2 grupos con ≥2 datos"}
    data = list(arrs.values())
    f, p_anova = _st.f_oneway(*data)
    h, p_kw = _st.kruskal(*data)
    # η² (tamaño de efecto de ANOVA).
    grand = np.concatenate(data)
    ss_total = float(np.sum((grand - grand.mean()) ** 2))
    ss_between = float(sum(v.size * (v.mean() - grand.mean()) ** 2 for v in data))
    eta2 = ss_between / ss_total if ss_total > 0 else 0.0
    return {
        "grupos": {k: {"n": int(v.size), "media": float(v.mean()),
                        "mediana": float(np.median(v))} for k, v in arrs.items()},
        "anova": {"F": float(f), "p": float(p_anova), "eta2": eta2,
                  "significativo": bool(p_anova < 0.05)},
        "kruskal": {"H": float(h), "p": float(p_kw), "significativo": bool(p_kw < 0.05)},
        "efecto": ("grande" if eta2 >= .14 else "medio" if eta2 >= .06 else "pequeño"),
    }


# --------------------------------------------------------------------------- #
#  Proporciones — CLAVE ELECTORAL
# --------------------------------------------------------------------------- #

def proportion_ci(k: int, n: int, *, conf: float = 0.95, population: int | None = None) -> dict:
    """Estimación de proporción + intervalo de Wilson + MARGEN DE ERROR.

    Ideal para intención de voto: `k` casos de `n`. Con `population` aplica la
    corrección por población finita (universo conocido)."""
    if n <= 0:
        return {"motivo": "n debe ser > 0"}
    p = k / n
    z = z_crit(conf)
    # Wilson (recomendado, estable en extremos y n chico).
    denom = 1 + z ** 2 / n
    center = (p + z ** 2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / denom
    lo, hi = center - half, center + half
    # Margen de error (aprox. normal), con corrección por población finita.
    fpc = math.sqrt((population - n) / (population - 1)) if population and population > n else 1.0
    moe = z * math.sqrt(p * (1 - p) / n) * fpc
    return {
        "k": int(k), "n": int(n), "p": float(p), "conf": conf,
        "wilson": [float(lo), float(hi)],
        "margen_error": float(moe),          # ± (proporción)
        "margen_error_pct": float(moe * 100),
        "ic_normal": [float(p - moe), float(p + moe)],
        "fpc": float(fpc), "poblacion": population,
    }


def margin_of_error(n: int, *, p: float = 0.5, conf: float = 0.95,
                    population: int | None = None) -> dict:
    """Margen de error de una encuesta de tamaño `n` (peor caso p=0.5)."""
    if n <= 0:
        return {"motivo": "n debe ser > 0"}
    z = z_crit(conf)
    fpc = math.sqrt((population - n) / (population - 1)) if population and population > n else 1.0
    moe = z * math.sqrt(p * (1 - p) / n) * fpc
    return {"n": int(n), "p": p, "conf": conf, "margen_error": float(moe),
            "margen_error_pct": float(moe * 100), "fpc": float(fpc)}


def sample_size_for_moe(moe: float, *, p: float = 0.5, conf: float = 0.95,
                        population: int | None = None) -> dict:
    """Tamaño de muestra para un margen de error objetivo (con población finita opcional)."""
    if not 0 < moe < 1:
        return {"motivo": "moe debe estar en (0,1)"}
    z = z_crit(conf)
    n0 = (z ** 2 * p * (1 - p)) / (moe ** 2)
    n = n0 / (1 + (n0 - 1) / population) if population else n0
    return {"n": int(math.ceil(n)), "moe": moe, "conf": conf,
            "p": p, "poblacion": population}


# --------------------------------------------------------------------------- #
#  Orquestador: estadística según la FORMA del resultado
# --------------------------------------------------------------------------- #

def summarize_result(shape: str, rows: list[dict], columns: list[str],
                     *, value_col: str | None = None, label_col: str | None = None) -> dict:
    """Ejecuta la batería estadística que corresponde a la forma del resultado.

    `shape`: "scalar" | "category" | "timeseries" | "correlation" | "distribution".
    Devuelve un bloque estructurado (solo números + banderas) para el informe."""
    out: dict[str, Any] = {"shape": shape, "n_filas": len(rows)}
    if not rows:
        return out
    cols = columns or list(rows[0].keys())
    # Heurística de columnas: última numérica = valor; primera no numérica = etiqueta.
    def _is_num(col):
        return all(_f(r.get(col)) is not None for r in rows if r.get(col) is not None)
    num_cols = [c for c in cols if _is_num(c)]
    cat_cols = [c for c in cols if c not in num_cols]
    vcol = value_col or (num_cols[-1] if num_cols else None)
    lcol = label_col or (cat_cols[0] if cat_cols else None)

    if vcol:
        vals = [r.get(vcol) for r in rows]

    if shape == "scalar" and vcol:
        out["valor"] = _f(rows[0].get(vcol))

    elif shape == "timeseries" and vcol:
        labels = [r.get(lcol) for r in rows] if lcol else None
        out["descriptivos"] = describe(vals)
        out["tendencia"] = trend(vals, labels=labels)

    elif shape == "category" and vcol:
        labels = [r.get(lcol) for r in rows] if lcol else [str(i) for i in range(len(rows))]
        out["descriptivos"] = describe(vals)
        out["categorico"] = categorical_summary(labels, vals)
        out["atipicos"] = outliers(vals)

    elif shape in ("correlation", "distribution"):
        if shape == "correlation" and len(num_cols) >= 2:
            xs = [r.get(num_cols[0]) for r in rows]
            ys = [r.get(num_cols[1]) for r in rows]
            out["correlacion"] = correlation(xs, ys)
        if vcol:
            out["descriptivos"] = describe(vals)
            out["normalidad"] = normality(vals)
            out["atipicos"] = outliers(vals)

    else:  # fallback: describe si hay numérico.
        if vcol:
            out["descriptivos"] = describe(vals)

    # Cautelas transversales.
    cautelas = []
    d = out.get("descriptivos")
    if d and d.get("n", 0) and d["n"] < 30:
        cautelas.append(f"Muestra pequeña (n={d['n']}): poca potencia; interpreta con cautela.")
    if out.get("correlacion", {}).get("significativa"):
        cautelas.append("Correlación no implica causación: puede haber confusión o causa inversa.")
    out["cautelas"] = cautelas
    return out
