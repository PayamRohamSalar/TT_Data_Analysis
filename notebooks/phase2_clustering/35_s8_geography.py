"""فاز ۲ - S8: جغرافیا؛ ترکیب خوشه‌ها به تفکیک استان و شعبه‌ی مبنای مشتری (1404، بدون DB).
شعبه‌ی مبنای مشتری از `home_branch`/`province` ذخیره‌ی ویژگی (پوشش حدود 84٪ مشتریان).
خروجی: s8_*.csv و reports/figures/phase2_clustering/ch8_*.png"""
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter, ScalarFormatter
from scipy.stats import spearmanr, chi2_contingency
from tt_bank.common.persian_plot import FONTS_DIR, setup_persian_font, to_persian_digits

ROOT = Path(__file__).resolve().parents[2]; D = ROOT / "data" / "processed" / "phase2_clustering"; P1 = ROOT / "data" / "processed" / "phase1_market_overview"; FIG = ROOT / "reports" / "figures" / "phase2_clustering"
setup_persian_font(); font_manager.fontManager.addfont(str(FONTS_DIR / "Vazirmatn-Bold.ttf"))
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 10, "savefig.dpi": 200, "axes.grid": False, "axes.axisbelow": True})
fd = to_persian_digits; BLUE, ORANGE, GREEN, RED, GREY = "#1F4E79", "#C55A11", "#548235", "#B03A2E", "#7F7F7F"
def save(fig, name):
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            if isinstance(axis.get_major_formatter(), ScalarFormatter): axis.set_major_formatter(FuncFormatter(lambda v, pos: fd(f"{v:g}")))
    fig.savefig(FIG / name, bbox_inches="tight", facecolor="white"); plt.close(fig); print("saved", name)
norm = lambda s: s.replace("ي", "ی").replace("ك", "ک").replace("‌", " ").strip()
H = 1e13; SEG = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "T", "I", "N", "S"]

F = pd.read_pickle(D / "features_customer_year.pkl"); F = F[F.y == 1404]
seg = pd.read_pickle(D / "cluster_assignments_1404.pkl")[["customer_id", "segment"]]
G = F.merge(seg, on="customer_id"); G["segment"] = G.segment.replace({"O": "I"}); G["province"] = G.province.map(lambda s: norm(s) if isinstance(s, str) else s)
G["dep"] = G.bal_dec.fillna(0); G["loan"] = G.loan_dec_r.fillna(0); G["npl"] = G.npl_dec_r.fillna(0)
N = len(G); A = G[G.province.notna()].copy()
print("پوشش شعبه/استان: %.4f مشتریان؛ %.4f سپرده؛ %.4f تسهیلات؛ %.4f غیرجاری" % (len(A) / N, A.dep.sum() / G.dep.sum(), A.loan.sum() / G.loan.sum(), A.npl.sum() / G.npl.sum()))
cov = G.groupby("segment").apply(lambda g: pd.Series(dict(customers=len(g), coverage=g.province.notna().mean(), deposit_cov=g.loc[g.province.notna(), "dep"].sum() / max(g.dep.sum(), 1)))).reindex(SEG)
cov.to_csv(D / "s8_coverage_by_segment.csv"); print(cov.round(3).to_string())

# ---------- جدول 8-1: ترکیب خوشه‌ها در استان (درصد مشتریان استان)
ct = pd.crosstab(A.province, A.segment).reindex(columns=SEG).fillna(0).astype(int)
pct = ct.div(ct.sum(1), axis=0) * 100; pct.round(2).to_csv(D / "s8_province_segment_pct.csv"); ct.to_csv(D / "s8_province_segment_counts.csv")
# سهم هر استان از هر خوشه (ستونی)
colpct = ct.div(ct.sum(0), axis=1) * 100; colpct.round(2).to_csv(D / "s8_province_segment_colpct.csv")
chi2, pval, dof, _ = chi2_contingency(ct.loc[~ct.index.isin(["ستاد", "شعب مستقل"])].to_numpy()); k = min(ct.shape) - 1
cv = np.sqrt(chi2 / (ct.to_numpy().sum() * k)); print("وابستگی استان و خوشه: Cramer's V = %.3f (n=%d)" % (cv, ct.to_numpy().sum()))
# نمایه‌های استانی نمونه
rows = []
for p, g in A.groupby("province"):
    b = g[g.loan > 0]
    rows.append(dict(province=p, customers=len(g), deposit_hemat=g.dep.sum() / H, loan_hemat=g.loan.sum() / H, npl_hemat=g.npl.sum() / H,
                     npl_ratio=g.npl.sum() / g.loan.sum() * 100 if g.loan.sum() > 0 else np.nan, ldr=g.loan.sum() / g.dep.sum() * 100 if g.dep.sum() > 0 else np.nan,
                     share_C1S=g.segment.isin(["C1", "S"]).mean() * 100, share_T=(g.segment == "T").mean() * 100, share_C7T=g.segment.isin(["C7", "T"]).mean() * 100,
                     share_borrowers=len(b) / len(g) * 100, deposit_share_C1S=g.loc[g.segment.isin(["C1", "S"]), "dep"].sum() / max(g.dep.sum(), 1) * 100,
                     npl_share_C1=g.loc[g.segment == "C1", "npl"].sum() / max(g.npl.sum(), 1) * 100, npl_share_T=g.loc[g.segment == "T", "npl"].sum() / max(g.npl.sum(), 1) * 100,
                     dominant=pct.loc[p, [s for s in SEG if s not in ("I", "N", "S")]].idxmax()))
PI = pd.DataFrame(rows).set_index("province"); P1d = pd.read_csv(P1 / "ch7_province_indicators.csv", encoding="utf-8-sig"); P1d["province"] = P1d.province.map(norm); P1d = P1d.set_index("province")
J = PI.join(P1d[["res_share", "loan_share", "ldr", "npl_ratio", "branches", "res_mult", "loan_mult"]].add_prefix("p1_"), how="left"); J.to_csv(D / "s8_province_indicators.csv")
print(J.round(2).to_string())
core = J[J.p1_res_share.notna()]
cor = {}
for a, b in [("npl_ratio", "p1_npl_ratio"), ("ldr", "p1_ldr"), ("deposit_hemat", "p1_res_share"), ("loan_hemat", "p1_loan_share"), ("share_C1S", "p1_res_mult"), ("share_C7T", "p1_npl_ratio"), ("share_T", "p1_npl_ratio"), ("share_C7T", "p1_ldr")]:
    r, p = spearmanr(core[a], core[b]); cor[f"{a} ~ {b}"] = (r, p, len(core))
CR = pd.DataFrame(cor, index=["spearman", "p", "n"]).T; CR.to_csv(D / "s8_correlation_with_phase1.csv"); print("\nهمبستگی رتبه‌ای با شاخص‌های فاز 1:\n", CR.round(3).to_string())

# ---------- تمرکز شعب
br = A.groupby("home_branch").agg(customers=("customer_id", "size"), dep=("dep", "sum"), loan=("loan", "sum"), npl=("npl", "sum"))
for s in ["C1", "C7", "T", "C4", "C2"]:
    br["n_" + s] = A[A.segment == s].groupby("home_branch").size().reindex(br.index).fillna(0)
nb = len(br); rows = []
def topshare(v, f): v = np.sort(v.to_numpy())[::-1]; return v[: max(1, int(round(nb * f)))].sum() / v.sum()
for lab, col in [("مشتریان", "customers"), ("سپرده", "dep"), ("تسهیلات", "loan"), ("غیرجاری", "npl"), ("مشتریان C1", "n_C1"), ("مشتریان C2", "n_C2"), ("مشتریان C4", "n_C4"), ("مشتریان C7", "n_C7"), ("مشتریان T", "n_T")]:
    rows.append(dict(item=lab, top10pct_branches=topshare(br[col], .10), top20pct_branches=topshare(br[col], .20), top_branch=br[col].max() / br[col].sum()))
BT = pd.DataFrame(rows); BT.to_csv(D / "s8_branch_concentration.csv", index=False); print("\nشعب با تخصیص:", nb, "\n", BT.round(3).to_string())
br.to_csv(D / "s8_branch_table.csv")

# ---------- نمودارها
order = pct.assign(w=ct.sum(1)).sort_values("w", ascending=False).index
M = pct.loc[order, SEG].to_numpy()
fig, ax = plt.subplots(figsize=(10, 11)); im = ax.imshow(M, cmap="Blues", aspect="auto", vmin=0, vmax=30)
ax.set_xticks(range(len(SEG))); ax.set_xticklabels(SEG); ax.set_yticks(range(len(order))); ax.set_yticklabels(order, fontsize=9); ax.set_xlabel("خوشه")
cb = fig.colorbar(im, shrink=.6); cb.set_label("درصد مشتریان استان")
for i in range(M.shape[0]):
    for j in range(M.shape[1]): ax.text(j, i, fd(f"{M[i, j]:.0f}"), ha="center", va="center", fontsize=7, color="white" if M[i, j] > 20 else "black")
save(fig, "ch8_province_cluster_heatmap.png")

fig, axs = plt.subplots(1, 2, figsize=(11, 4.8))
for ax, (a, b, xl, yl) in zip(axs, [("npl_ratio", "p1_npl_ratio", "نسبت غیرجاری رسمی بانک (فاز 1، ٪)", "نسبت غیرجاری نمونه (٪)"), ("ldr", "p1_ldr", "نسبت وام به سپرده رسمی بانک (٪)", "نسبت وام به سپرده نمونه (٪)")]):
    ax.scatter(core[b], core[a], color=BLUE, s=28); r = spearmanr(core[a], core[b])[0]; ax.set_xlabel(xl); ax.set_ylabel(yl); ax.set_title("همبستگی رتبه‌ای " + fd(f"{r:.2f}"))
    if a == "ldr": ax.set_yscale("log"); ax.set_xscale("log")
save(fig, "ch8_sample_vs_phase1.png")

fig, ax = plt.subplots(figsize=(10, 4.6)); x = np.arange(len(BT)); w = .4
ax.bar(x - w / 2, BT.top10pct_branches * 100, w, color=BLUE, label="10٪ شعب بزرگ"); ax.bar(x + w / 2, BT.top20pct_branches * 100, w, color=ORANGE, label="20٪ شعب بزرگ")
ax.set_xticks(x); ax.set_xticklabels(BT.item, rotation=20, ha="right"); ax.set_ylabel("سهم از کل (٪)"); ax.legend(frameon=False); save(fig, "ch8_branch_concentration.png")
