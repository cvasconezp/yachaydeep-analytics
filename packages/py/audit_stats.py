"""
Auditoría de EXACTITUD de yd_analytics.stats contra referencias independientes:
statsmodels, pymannkendall, scipy directo y fórmulas a mano.

No es el test suite del repo: es una verificación adversarial de que cada número
que producimos coincide con el estándar de oro. Contexto electoral => cero tolerancia.
"""
import math
import numpy as np
from scipy import stats as st
import statsmodels.api as sm
from statsmodels.stats.proportion import proportion_confint
from statsmodels.stats.weightstats import DescrStatsW
import pymannkendall as pmk

from yd_analytics import stats as S

RTOL = 1e-9
ATOL = 1e-9
fails, checks = [], 0

def chk(name, got, exp, rtol=RTOL, atol=ATOL):
    global checks
    checks += 1
    ok = np.allclose(got, exp, rtol=rtol, atol=atol)
    if not ok:
        fails.append((name, got, exp))
        print(f"  ✗ {name}: got={got!r} exp={exp!r}")
    else:
        print(f"  ✓ {name}")

rng = np.random.default_rng(42)

# --------------------------------------------------------------- describe
print("== describe ==")
x = list(rng.normal(50, 12, 37)) + [120.0, -8.0]  # con cola/atípicos
d = S.describe(x)
xa = np.array([float(v) for v in x])
chk("media", d["media"], np.mean(xa))
chk("mediana", d["mediana"], np.median(xa))
chk("std (ddof=1)", d["std"], np.std(xa, ddof=1))
chk("var (ddof=1)", d["var"], np.var(xa, ddof=1))
chk("sem", d["sem"], np.std(xa, ddof=1)/math.sqrt(xa.size))
chk("skew", d["asimetria"], st.skew(xa))
chk("kurtosis(exceso)", d["curtosis"], st.kurtosis(xa))
chk("p25", d["q1"], np.percentile(xa,25))
chk("p75", d["q3"], np.percentile(xa,75))
chk("cv", d["cv"], np.std(xa,ddof=1)/np.mean(xa))
# IC de la media t contra statsmodels DescrStatsW
lo, hi = DescrStatsW(xa).tconfint_mean(alpha=0.05)
chk("ic95_media.lo", d["ic95_media"][0], lo)
chk("ic95_media.hi", d["ic95_media"][1], hi)

# --------------------------------------------------------------- outliers
print("== outliers (IQR 1.5x, z>3) ==")
q1, q3 = np.percentile(xa,25), np.percentile(xa,75)
iqr = q3-q1; lo_, hi_ = q1-1.5*iqr, q3+1.5*iqr
exp_iqr = int(((xa<lo_)|(xa>hi_)).sum())
o = S.outliers(x)
chk("iqr.n", o["iqr"]["n"], exp_iqr)
chk("iqr.limite_inf", o["iqr"]["limite_inf"], lo_)
chk("iqr.limite_sup", o["iqr"]["limite_sup"], hi_)
z = (xa-xa.mean())/np.std(xa,ddof=1)
chk("zscore.n", o["zscore"]["n"], int((np.abs(z)>3).sum()))

# --------------------------------------------------------------- trend / OLS
print("== trend (OLS) vs statsmodels ==")
y = np.array([10, 12, 11.5, 14, 15.2, 15.0, 17.3, 18.9], dtype=float)
idx = np.arange(y.size, dtype=float)
X = sm.add_constant(idx)
res = sm.OLS(y, X).fit()
t = S.trend(list(y))
chk("pendiente (slope)", t["pendiente"], res.params[1])
chk("intercepto", t["intercepto"], res.params[0])
chk("r2", t["r2"], res.rsquared)
chk("p (slope)", t["p"], res.pvalues[1])
chk("err_pendiente", t["err_pendiente"], res.bse[1])
# CAGR a mano
chk("cagr_pct", t["cagr_pct"], ((y[-1]/y[0])**(1/(y.size-1))-1)*100)
chk("cambio_total_pct", t["cambio_total_pct"], (y[-1]-y[0])/abs(y[0])*100)
# pronostico = slope*n+intercept
chk("pronostico_siguiente", t["pronostico_siguiente"], res.params[1]*y.size+res.params[0])

# --------------------------------------------------------------- Mann-Kendall
print("== Mann-Kendall vs pymannkendall ==")
for name, series in [("monotona", y),
                     ("con empates", np.array([3,3,4,4,5,5,2,2,6,6,7,7], float)),
                     ("ruido", rng.normal(0,1,20))]:
    mk = S.mann_kendall(list(series))
    ref = pmk.original_test(np.asarray(series))
    chk(f"MK.S [{name}]", mk["S"], ref.s)
    chk(f"MK.z [{name}]", mk["z"], ref.z)
    chk(f"MK.p [{name}]", mk["p"], ref.p)
    chk(f"MK.tau [{name}]", mk["tau"], ref.Tau)

# --------------------------------------------------------------- correlacion
print("== correlacion vs scipy ==")
a = rng.normal(0,1,40); b = 0.7*a + rng.normal(0,0.5,40)
c = S.correlation(list(a), list(b))
pr,pp = st.pearsonr(a,b); sr,sp = st.spearmanr(a,b)
chk("pearson_r", c["pearson_r"], pr)
chk("pearson_p", c["pearson_p"], pp)
chk("spearman_rho", c["spearman_rho"], sr)
chk("spearman_p", c["spearman_p"], sp)

# --------------------------------------------------------------- categorico
print("== categorical_summary (HHI, Gini, entropia, chi2) ==")
labs = ["A","B","C","D","E","F"]
cnts = [1180,1620,540,610,290,760]
cs = S.categorical_summary(labs, cnts)
c_ = np.array(cnts, float); tot=c_.sum(); sh=c_/tot
chk("HHI", cs["hhi"], float(np.sum(sh**2)))
# Gini de referencia (definicion de media de diferencias absolutas)
def gini_ref(v):
    v = np.sort(np.asarray(v, float)); n=v.size; cum=np.cumsum(v)
    return (n+1-2*np.sum(cum)/cum[-1])/n
chk("Gini", cs["gini"], gini_ref(c_))
# entropia Shannon normalizada
ent = -np.sum(sh*np.log(sh))/math.log(len(cnts))
chk("entropia_norm", cs["entropia"], ent)
# chi2 bondad de ajuste uniforme
chi2_ref, p_ref = st.chisquare(c_, np.full(len(cnts), tot/len(cnts)))
chk("chi2_uniformidad", cs["chi2_uniformidad"]["chi2"], chi2_ref)
chk("chi2_uniformidad.p", cs["chi2_uniformidad"]["p"], p_ref)

# --------------------------------------------------------------- chi2 indep + Cramer
print("== chi2_independence + Cramer's V ==")
tab = [[30,10,20],[15,25,10],[5,15,25]]
ci = S.chi_square_independence(tab)
chi2r,pr2,dofr,expr = st.chi2_contingency(np.array(tab,float))
chk("chi2", ci["chi2"], chi2r)
chk("dof", ci["dof"], dofr)
chk("p", ci["p"], pr2)
arr=np.array(tab,float); nn=arr.sum(); r,cc=arr.shape
chk("cramers_v", ci["cramers_v"], math.sqrt(chi2r/(nn*(min(r,cc)-1))))

# --------------------------------------------------------------- grupos
print("== compare_groups (ANOVA, Kruskal, eta2) ==")
g = {"g1": list(rng.normal(10,2,15)), "g2": list(rng.normal(12,2,15)), "g3": list(rng.normal(11,2,15))}
cg = S.compare_groups(g)
data=[np.array(v,float) for v in g.values()]
f,pa = st.f_oneway(*data); h,pk = st.kruskal(*data)
chk("ANOVA.F", cg["anova"]["F"], f)
chk("ANOVA.p", cg["anova"]["p"], pa)
chk("Kruskal.H", cg["kruskal"]["H"], h)
chk("Kruskal.p", cg["kruskal"]["p"], pk)
grand=np.concatenate(data)
sst=np.sum((grand-grand.mean())**2)
ssb=sum(v.size*(v.mean()-grand.mean())**2 for v in data)
chk("eta2", cg["anova"]["eta2"], ssb/sst)

# --------------------------------------------------------------- PROPORCIONES (electoral)
print("== proportion_ci: Wilson vs statsmodels + MoE + FPC ==")
for k,n in [(1360,4000),(34,100),(2,50),(500,1000)]:
    r = S.proportion_ci(k,n)
    wlo,whi = proportion_confint(k,n,alpha=0.05,method="wilson")
    chk(f"Wilson.lo [{k}/{n}]", r["wilson"][0], wlo)
    chk(f"Wilson.hi [{k}/{n}]", r["wilson"][1], whi)
    p=k/n; z=st.norm.ppf(0.975)
    chk(f"MoE [{k}/{n}]", r["margen_error"], z*math.sqrt(p*(1-p)/n))
# FPC
pop=13_500_000; k,n=1360,4000
r = S.proportion_ci(k,n,population=pop)
fpc=math.sqrt((pop-n)/(pop-1)); p=k/n; z=st.norm.ppf(0.975)
chk("FPC", r["fpc"], fpc)
chk("MoE con FPC", r["margen_error"], z*math.sqrt(p*(1-p)/n)*fpc)

print("== margin_of_error + sample_size ==")
m = S.margin_of_error(1068)   # clasico ~3%
chk("MoE(n=1068,p=.5)", m["margen_error_pct"], st.norm.ppf(0.975)*math.sqrt(0.25/1068)*100)
ss = S.sample_size_for_moe(0.03)
n0 = (st.norm.ppf(0.975)**2*0.25)/0.03**2
chk("n para MoE 3%", ss["n"], math.ceil(n0))
ss2 = S.sample_size_for_moe(0.03, population=50000)
n_fin = n0/(1+(n0-1)/50000)
chk("n para MoE 3% (pob finita)", ss2["n"], math.ceil(n_fin))

# 99% de confianza cambia z
print("== niveles de confianza ==")
chk("z 95%", S.z_crit(0.95), st.norm.ppf(0.975))
chk("z 99%", S.z_crit(0.99), st.norm.ppf(0.995))
chk("z 90%", S.z_crit(0.90), st.norm.ppf(0.95))

print(f"\n{'='*50}\n{checks} verificaciones · {len(fails)} discrepancias")
if fails:
    for n_,g_,e_ in fails: print("  FALLO:", n_)
    raise SystemExit(1)
print("EXACTITUD CONFIRMADA: todo coincide con statsmodels/pymannkendall/scipy.")
