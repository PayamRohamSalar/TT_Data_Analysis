"""فاز ۲ - S6: ارزش اقتصادی و ریسک خوشه‌ها (1404، بدون DB).
جدول 6-1 (سهم مشتری، سپرده، وام، غیرجاری، سود)، جدول 6-2 (ظرفیت فروش تسهیلات)، منحنی تمرکز، نمودارهای ch6_*.
ورودی: features_customer_year.pkl، cluster_assignments_1404.pkl. خروجی: s6_*.csv و reports/figures/phase2_clustering/ch6_*.png"""
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter, ScalarFormatter
from tt_bank.common.persian_plot import FONTS_DIR, setup_persian_font, to_persian_digits

ROOT = Path(__file__).resolve().parents[2]; D = ROOT / "data" / "processed" / "phase2_clustering"; FIG = ROOT / "reports" / "figures" / "phase2_clustering"
setup_persian_font(); font_manager.fontManager.addfont(str(FONTS_DIR / "Vazirmatn-Bold.ttf"))
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 11, "savefig.dpi": 200, "axes.grid": True, "grid.color": "#E6E6E6", "axes.axisbelow": True})
fd = to_persian_digits; BLUE, ORANGE, GREEN, RED, GREY = "#1F4E79", "#C55A11", "#548235", "#B03A2E", "#7F7F7F"
def save(fig, name):
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            f = axis.get_major_formatter()
            if isinstance(f, ScalarFormatter): axis.set_major_formatter(FuncFormatter(lambda v, pos: fd(f"{v:g}")))
    fig.savefig(FIG / name, bbox_inches="tight", facecolor="white"); plt.close(fig); print("saved", name)

F = pd.read_pickle(D / "features_customer_year.pkl"); F = F[F.y == 1404]
seg = pd.read_pickle(D / "cluster_assignments_1404.pkl")[["customer_id", "segment"]]
G = F.merge(seg, on="customer_id", how="inner"); G["segment"] = G.segment.replace({"O": "I"})
assert len(G) == 712908
ORDER = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "T", "I", "N", "S"]
G["dep"] = G.bal_dec.fillna(0); G["loan"] = G.loan_dec_r.fillna(0); G["npl"] = G.npl_dec_r.fillna(0)
H = 1e13  # همت = 1e12 تومان = 1e13 ریال
TOT = dict(customers=len(G), dep=G.dep.sum() / H, loan=G.loan.sum() / H, npl=G.npl.sum() / H)
print("جمع:", {k: round(v, 3) for k, v in TOT.items()})

# ---------- جدول 6-1
rows = []
for s in ORDER:
    g = G[G.segment == s]; b = g[g.loan > 0]; it = g[g.has_interest == 1]
    rows.append(dict(segment=s, customers=len(g), share_customers=len(g) / TOT["customers"],
                     deposit_hemat=g.dep.sum() / H, share_deposit=g.dep.sum() / H / TOT["dep"],
                     loan_hemat=g.loan.sum() / H, share_loan=g.loan.sum() / H / TOT["loan"],
                     npl_hemat=g.npl.sum() / H, share_npl=g.npl.sum() / H / TOT["npl"], npl_ratio=g.npl.sum() / g.loan.sum() if g.loan.sum() > 0 else np.nan,
                     borrowers=len(b), share_borrowers=len(b) / len(g), loan_to_deposit=g.loan.sum() / g.dep.sum() if g.dep.sum() > 0 else np.nan,
                     mean_deposit_mtoman=g.dep.mean() / 1e7, median_deposit_mtoman=g.dep.median() / 1e7,
                     mean_loan_borrower_mtoman=b.loan.mean() / 1e7 if len(b) else np.nan,
                     interest_coverage=len(it) / len(g), interest_share_of_total=it.interest_sum_r.sum() / G[G.has_interest == 1].interest_sum_r.sum(),
                     interest_per_deposit=it.interest_sum_r.sum() / max(it.dep.sum(), 1),
                     late30=b.late30_share.mean(), late90=b.late90_share.mean(), ledger_cov=b.has_ledger.mean()))
T1 = pd.DataFrame(rows); T1.to_csv(D / "s6_table_6_1.csv", index=False)
chk = {c: T1[c].sum() for c in ["share_customers", "share_deposit", "share_loan", "share_npl", "interest_share_of_total"]}
print("جمع سهم‌ها:", {k: round(v, 4) for k, v in chk.items()})
pd.set_option("display.width", 300, "display.max_columns", 40); print(T1.round(3).to_string())

# ---------- منحنی تمرکز
def conc(x):
    x = np.sort(x)[::-1]; c = np.cumsum(x) / x.sum(); n = len(x); gini = 1 - 2 * np.trapz(np.cumsum(np.sort(x)) / x.sum(), dx=1 / n) if False else None
    xs = np.sort(x); lor = np.cumsum(xs) / xs.sum(); gini = 1 - 2 * lor.mean() + 1 / n
    return c, gini
cd, gd = conc(G.dep.to_numpy()); cl, gl = conc(G.loan.to_numpy()); cn, gn = conc(G.npl.to_numpy())
n = len(G); q = {f: (cd[int(n * f) - 1], cl[int(n * f) - 1], cn[int(n * f) - 1]) for f in (.001, .01, .05, .10)}
bor = G[G.loan > 0]; cb, gb = conc(bor.loan.to_numpy()); nb = len(bor)
qb = {f: cb[int(nb * f) - 1] for f in (.01, .05, .10)}
conc_tab = [dict(top_fraction=f, deposit=v[0], loan_all_customers=v[1], npl_all_customers=v[2], loan_among_borrowers=qb.get(f, np.nan)) for f, v in q.items()]
pd.DataFrame(conc_tab).to_csv(D / "s6_concentration.csv", index=False)
print("تمرکز:", pd.DataFrame(conc_tab).round(3).to_string(), "\nGini سپرده %.3f وام(همه) %.3f وام(وام‌گیران) %.3f غیرجاری(همه) %.3f" % (gd, gl, gb, gn))
fig, ax = plt.subplots(figsize=(7, 5.2)); xs = np.arange(1, n + 1) / n * 100
idx = np.unique(np.r_[np.arange(0, n, 500), n - 1])
ax.plot(xs[idx], cd[idx] * 100, color=BLUE, label="مانده‌ی سپرده"); ax.plot(xs[idx], cl[idx] * 100, color=GREEN, label="مانده‌ی تسهیلات")
ax.plot(xs[idx], cn[idx] * 100, color=RED, label="مانده‌ی غیرجاری"); ax.plot([0, 100], [0, 100], color=GREY, ls="--", lw=1)
ax.set_xlabel("درصد مشتریان (از بزرگ‌ترین مانده)"); ax.set_ylabel("سهم تجمعی (درصد)"); ax.legend(frameon=False); ax.set_xscale("log"); ax.set_xlim(0.01, 100); ax.set_xticks([0.01, 0.1, 1, 10, 100]); ax.set_xticklabels([fd(t) for t in ["0.01", "0.1", "1", "10", "100"]]); ax.set_ylim(0, 100); ax.set_xlabel("درصد مشتریان (از بزرگ‌ترین مانده، مقیاس لگاریتمی)"); save(fig, "ch6_concentration_curve.png")

# ---------- جدول 6-2: ظرفیت فروش تسهیلات
main = G[G.segment.isin(["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"])]
thr = main[main.loan > 0].bal_mean_r.median()  # میانه‌ی مانده‌ی میانگین وام‌گیران خوشه‌های اصلی
nl = G[(G.has_primary_loan == 0) & (G.loan == 0) & G.segment.isin(["C1", "C3", "C5", "C6", "C4"])]
rows2 = []
for s in ["C1", "C3", "C4", "C5", "C6"]:
    g = nl[nl.segment == s]; e = g[g.bal_mean_r >= thr]; ref = G[(G.segment == s) & (G.loan > 0)]
    ref_loan = ref.loan.median() if len(ref) else np.nan; e100 = g[g.bal_mean_r >= 1e9]
    rows2.append(dict(segment=s, no_loan_customers=len(g), eligible=len(e), eligible_share_of_segment=len(e) / (G.segment == s).sum(), eligible_deposit_hemat=e.dep.sum() / H,
                      median_balance_mtoman=e.bal_mean_r.median() / 1e7 if len(e) else np.nan, borrower_median_loan_mtoman=ref_loan / 1e7 if len(ref) else np.nan,
                      reference_ceiling_hemat=len(e) * ref_loan / H if len(ref) else np.nan, eligible_100mt=len(e100), eligible_100mt_deposit_hemat=e100.dep.sum() / H, churn_trend=e.bal_trend.mean() if len(e) else np.nan))
T2 = pd.DataFrame(rows2); T2.to_csv(D / "s6_table_6_2.csv", index=False)
print("آستانه‌ی ظرفیت (میانه‌ی مانده‌ی میانگین وام‌گیران) = %.2f میلیون تومان" % (thr / 1e7)); print(T2.round(3).to_string())

# ---------- نمودارها
x = np.arange(len(T1)); w = .2; lab = T1.segment.tolist()
fig, ax = plt.subplots(figsize=(11, 4.8))
for k, (c, col, t) in enumerate([("share_customers", BLUE, "سهم مشتریان"), ("share_deposit", ORANGE, "سهم سپرده"), ("share_loan", GREEN, "سهم تسهیلات"), ("share_npl", RED, "سهم غیرجاری")]):
    ax.bar(x + (k - 1.5) * w, T1[c] * 100, w, color=col, label=t)
ax.set_xticks(x); ax.set_xticklabels(lab); ax.set_ylabel("درصد"); ax.legend(frameon=False, ncol=4); ax.grid(axis="x", visible=False); save(fig, "ch6_count_vs_amount.png")

fig, ax = plt.subplots(figsize=(10, 4.6)); m = T1.npl_ratio.notna()
ax.bar(x[m] - .2, T1.npl_ratio[m] * 100, .4, color=RED, label="نسبت غیرجاری به تسهیلات (٪)"); ax.bar(x + .2, T1.share_npl * 100, .4, color=BLUE, label="سهم از کل مانده‌ی غیرجاری (٪)")
ax.set_xticks(x); ax.set_xticklabels(lab); ax.set_ylabel("درصد"); ax.legend(frameon=False); ax.grid(axis="x", visible=False); save(fig, "ch6_npl_by_cluster.png")

fig, ax = plt.subplots(figsize=(8.6, 6)); pp = T1[T1.segment != "I"]
sc = ax.scatter(pp.deposit_hemat, pp.loan_hemat, s=pp.customers / 400, c=pp.npl_ratio * 100, cmap="Reds", edgecolor=GREY, vmin=0, vmax=60)
for _, r in pp.iterrows(): ax.annotate(r.segment, (r.deposit_hemat, r.loan_hemat), ha="center", va="center", fontsize=9)
ax.set_xscale("symlog", linthresh=1); ax.set_xticks([0, 1, 10]); ax.set_xticklabels([fd(t) for t in ["0", "1", "10"]]); ax.set_xlabel("مانده‌ی سپرده (همت، مقیاس لگاریتمی)"); ax.set_ylabel("مانده‌ی تسهیلات (همت)"); cb_ = fig.colorbar(sc); cb_.set_label("نسبت غیرجاری (٪)")
save(fig, "ch6_bubble_deposit_loan_risk.png")

fig, ax = plt.subplots(figsize=(10, 4.6)); bsel = T1[T1.borrowers > 0]; xb = np.arange(len(bsel))
ax.bar(xb - .2, bsel.late30 * 100, .4, color=ORANGE, label="اقساط با تأخیر بیش از 30 روز (٪)"); ax.bar(xb + .2, bsel.late90 * 100, .4, color=RED, label="اقساط با تأخیر بیش از 90 روز (٪)")
ax.set_xticks(xb); ax.set_xticklabels(bsel.segment); ax.set_ylabel("درصد اقساط (میانگین وام‌گیران)"); ax.legend(frameon=False); ax.grid(axis="x", visible=False); save(fig, "ch6_late_payment.png")

fig, ax = plt.subplots(figsize=(10, 4.6)); isel = T1[T1.interest_coverage > 0]; xi = np.arange(len(isel))
ax.bar(xi, isel.interest_per_deposit * 100, .55, color=BLUE); ax.set_xticks(xi); ax.set_xticklabels(isel.segment); ax.set_ylabel("سود پرداختی به مانده‌ی سپرده (٪، فقط مشتریان دارای رکورد سود)"); ax.grid(axis="x", visible=False); save(fig, "ch6_interest_cost.png")
