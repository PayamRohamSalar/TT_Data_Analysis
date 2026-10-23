"""فاز ۲ - S4: کارت امتیاز اعتبارسنجی، رتبه‌بندی روش‌ها، حساسیت وزنی و نمودارهای فصل ۴ (بدون DB)."""
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter, ScalarFormatter
from sklearn.metrics import adjusted_rand_score
from tt_bank.common.persian_plot import FONTS_DIR, setup_persian_font, to_persian_digits

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data" / "processed" / "phase2_clustering"; LAB = D / "s4_labels"
FIG = ROOT / "reports" / "figures" / "phase2_clustering"; FIG.mkdir(parents=True, exist_ok=True)
setup_persian_font(); font_manager.fontManager.addfont(str(FONTS_DIR / "Vazirmatn-Bold.ttf"))
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 11, "savefig.dpi": 200, "axes.grid": True, "grid.color": "#E6E6E6", "axes.axisbelow": True})
fd = to_persian_digits
BLUE, ORANGE, GREEN, RED, GREY, PURPLE = "#1F4E79", "#C55A11", "#548235", "#B03A2E", "#7F7F7F", "#7B4F9D"
def save(fig, name):
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            f = axis.get_major_formatter()
            if isinstance(f, ScalarFormatter): axis.set_major_formatter(FuncFormatter(lambda v, pos: fd(f"{v:g}")))
            elif isinstance(f, FuncFormatter): axis.set_major_formatter(FuncFormatter(lambda v, pos, f=f: fd(f(v, pos))))
    fig.savefig(FIG / name, bbox_inches="tight", facecolor="white"); plt.close(fig); print("saved", name)
NAME = {"M1": "RFM قاعده‌ای", "M2": "K-Means روی RFM-L", "M3": "K-Means (همه‌ی ویژگی‌ها)", "M3n": "K-Means بدون وزن بلوک", "M4": "ترکیبی دومرحله‌ای",
        "M5": "مدل آمیخته‌ی گاوسی", "M6": "Ward (ریزخوشه)", "M7_3000": "HDBSCAN (3000)", "M7_8000": "HDBSCAN (8000)", "M8": "خوشه‌بندی مسیر", "M9": "اجماع"}

R = pd.read_csv(D / "s4_scorecard_raw.csv")
R = R.merge(pd.read_csv(D / "s4_tree_fidelity.csv"), on=["method", "k"], how="left")
R["method_fa"] = R.method.map(NAME)
OUTS = ["loan_uptake", "balance_halved", "dormant_next", "npl_entry"]
R["ext"] = R[[f"adjr2_{o}" for o in OUTS]].mean(axis=1)
R["lift_max"] = R[[f"lift_{o}" for o in OUTS]].mean(axis=1)
R.to_csv(D / "s4_scorecard_full.csv", index=False, encoding="utf-8-sig")

def score_frame(R_, w):
    """رتبه‌ی هر روش درون هر k در هر معیار → امتیاز 0 تا 1 → ترکیب وزنی؛ سپس میانگین روی k."""
    rows = []
    for k, g in R_.groupby("k"):
        if len(g) < 2: continue
        sc = pd.DataFrame(index=g.index)
        def rk(col, high=True):
            r = g[col].rank(ascending=not high, method="average", na_option="keep")
            return 1 - (r - 1) / (r.max() - 1) if r.max() > 1 else r * 0 + 0.5
        internal = pd.concat([rk("sil"), rk("ch"), rk("db", high=False)], axis=1).mean(axis=1)
        stability = pd.concat([rk("half_ari"), rk("temporal_ari")], axis=1).mean(axis=1)
        external = rk("ext")
        usability = pd.concat([rk("entropy"), rk("min_share"), rk("fidelity")], axis=1).mean(axis=1)
        comp = w["internal"] * internal.fillna(internal.mean()) + w["stability"] * stability.fillna(0.3) + w["external"] * external.fillna(0) + w["usability"] * usability.fillna(0.5)
        for idx in g.index:
            rows.append(dict(method=g.loc[idx, "method"], k=k, internal=internal[idx], stability=stability[idx], external=external[idx], usability=usability[idx], composite=comp[idx]))
    return pd.DataFrame(rows)

W = {"base": dict(internal=.25, stability=.30, external=.30, usability=.15),
     "equal": dict(internal=.25, stability=.25, external=.25, usability=.25),
     "external_heavy": dict(internal=.15, stability=.25, external=.45, usability=.15)}
S = {n: score_frame(R, w) for n, w in W.items()}
S["base"].to_csv(D / "s4_scores_by_k.csv", index=False)
rank = pd.DataFrame({n: s.groupby("method").composite.mean() for n, s in S.items()})
rank["rank_base"] = rank.base.rank(ascending=False); rank["rank_equal"] = rank.equal.rank(ascending=False); rank["rank_ext"] = rank.external_heavy.rank(ascending=False)
rank["borda"] = rank[["rank_base", "rank_equal", "rank_ext"]].mean(axis=1)
rank = rank.sort_values("borda"); rank.to_csv(D / "s4_method_ranking.csv", encoding="utf-8-sig")
print(rank.round(3).to_string())
best_k = S["base"].sort_values("composite", ascending=False).groupby("method").head(1).sort_values("composite", ascending=False)
best_k.to_csv(D / "s4_best_k_by_method.csv", index=False); print(best_k.round(3).to_string())

# ---- نمودارها
# 4-1: معیارهای داخلی K-Means بر حسب k
m3 = R[R.method == "M3"].sort_values("k")
fig, axes = plt.subplots(1, 3, figsize=(12.5, 3.8))
for ax, (c, t, col) in zip(axes, [("sil", "silhouette", BLUE), ("ch", "شاخص کالینسکی-هاراباز", GREEN), ("db", "شاخص دیویس-بولدین", RED)]):
    ax.plot(m3.k, m3[c], marker="o", color=col, lw=2); ax.set_title(t, fontsize=11); ax.set_xlabel("تعداد خوشه")
save(fig, "ch4_internal_metrics_vs_k.png")
# 4-4: پایداری
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.2), sharex=True)
cols = {"M3": BLUE, "M3n": GREY, "M2": ORANGE, "M4": GREEN, "M5": PURPLE, "M6": RED, "M8": "#2E86AB", "M9": "#999900"}
for m, c in cols.items():
    g = R[R.method == m].sort_values("k")
    if g.empty: continue
    axes[0].plot(g.k, g.half_ari, marker="o", color=c, label=NAME[m]); axes[1].plot(g.k, g.temporal_ari, marker="o", color=c, label=NAME[m])
axes[0].set_title("پایداری نیم‌نمونه (ARI)", fontsize=11); axes[1].set_title("پایداری زمانی ۱۴۰۳ به ۱۴۰۴ (ARI)", fontsize=11)
for ax in axes: ax.set_xlabel("تعداد خوشه")
fig.legend(*axes[1].get_legend_handles_labels(), loc="lower center", ncol=4, frameon=False, fontsize=9, bbox_to_anchor=(0.5, -0.12)); save(fig, "ch4_stability_vs_k.png")
# 4-9: اعتبار بیرونی
fig, ax = plt.subplots(figsize=(10.5, 4.6))
base_k = R[R.k.isin([6, 7, 8])].groupby("method")[[f"adjr2_{o}" for o in OUTS]].mean()
base_k = base_k.reindex([m for m in NAME if m in base_k.index])
x = np.arange(len(base_k)); wdt = .2
lab_fa = {"loan_uptake": "وام‌گیری سال بعد", "balance_halved": "نصف‌شدن مانده", "dormant_next": "راکد یا خروج", "npl_entry": "ورود به غیرجاری"}
for i, o in enumerate(OUTS):
    ax.bar(x + (i - 1.5) * wdt, base_k[f"adjr2_{o}"] * 100, wdt, label=lab_fa[o])
ax.set_xticks(x); ax.set_xticklabels([NAME[m] for m in base_k.index], rotation=25, ha="right", fontsize=9)
ax.set_ylabel("R² تعدیل‌شده (درصد)"); ax.legend(frameon=False, fontsize=9, ncol=4); save(fig, "ch4_external_validity.png")
# 4-8: ماتریس توافق در k=7
ms = [m for m in ["M1", "M2", "M3", "M3n", "M4", "M5", "M6", "M8", "M9"] if (LAB / f"{m}_k7_A.npy").exists()]
L = {m: np.load(LAB / f"{m}_k7_A.npy") for m in ms}
Mx = np.array([[adjusted_rand_score(L[a], L[b]) for b in ms] for a in ms])
pd.DataFrame(Mx, index=ms, columns=ms).to_csv(D / "s4_method_agreement_k7.csv")
fig, ax = plt.subplots(figsize=(7.5, 6.3)); im = ax.imshow(Mx, cmap="Blues", vmin=0, vmax=1); ax.grid(False)
ax.set_xticks(range(len(ms))); ax.set_yticks(range(len(ms))); ax.set_xticklabels([NAME[m] for m in ms], rotation=60, ha="right", fontsize=8.5); ax.set_yticklabels([NAME[m] for m in ms], fontsize=8.5)
for i in range(len(ms)):
    for j in range(len(ms)): ax.text(j, i, fd(f"{Mx[i, j]:.2f}"), ha="center", va="center", fontsize=8, color="white" if Mx[i, j] > .6 else "black")
fig.colorbar(im, shrink=.7); save(fig, "ch4_method_agreement.png")
# 4-10: حساسیت رتبه
fig, ax = plt.subplots(figsize=(9.5, 4.4)); xx = np.arange(len(rank)); w3 = .26
for i, (c, lab) in enumerate([("rank_base", "وزن پایه"), ("rank_equal", "وزن برابر"), ("rank_ext", "تأکید بر اعتبار بیرونی")]):
    ax.bar(xx + (i - 1) * w3, rank[c], w3, label=lab)
ax.set_xticks(xx); ax.set_xticklabels([NAME.get(m, m) for m in rank.index], rotation=25, ha="right", fontsize=9)
ax.set_ylabel("رتبه (۱ بهترین)"); ax.invert_yaxis(); ax.legend(frameon=False, fontsize=9); save(fig, "ch4_rank_sensitivity.png")
