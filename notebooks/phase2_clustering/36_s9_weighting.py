"""فاز ۲ - S9: وزن‌دهی و حساسیت تعمیم (بدون DB).
۱) آزمون سازگاری طبقات سپرده و وام RFM بانک (09/1404) با نمونه؛ ۲) وزن طبقه‌ی وام و وزن استانی؛ ۳) وزن‌دهی تکراری (raking) وام: طبقه × استان؛ ۴) سهم وزن‌دار خوشه‌ها.
ورودی: customer_month_deposit.pkl، customer_month_loan_v2.pkl، features_customer_year.pkl، cluster_assignments_1404.pkl، آمار رسمی فاز 1 (RFM بانک، استان). خروجی: s9_*.csv و ch9_*.png"""
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter, ScalarFormatter
from tt_bank.common.persian_plot import FONTS_DIR, setup_persian_font, to_persian_digits

ROOT = Path(__file__).resolve().parents[2]; D = ROOT / "data" / "processed" / "phase2_clustering"; P1 = ROOT / "data" / "processed" / "phase1_market_overview"; FIG = ROOT / "reports" / "figures" / "phase2_clustering"
setup_persian_font(); font_manager.fontManager.addfont(str(FONTS_DIR / "Vazirmatn-Bold.ttf"))
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 11, "savefig.dpi": 200, "axes.grid": False})
fd = to_persian_digits; BLUE, ORANGE, GREEN, RED, GREY = "#1F4E79", "#C55A11", "#548235", "#B03A2E", "#7F7F7F"
def save(fig, name):
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            if isinstance(axis.get_major_formatter(), ScalarFormatter): axis.set_major_formatter(FuncFormatter(lambda v, pos: fd(f"{v:g}")))
    fig.savefig(FIG / name, bbox_inches="tight", facecolor="white"); plt.close(fig); print("saved", name)
norm = lambda s: s.replace("ي", "ی").replace("ك", "ک").replace("‌", " ").strip()
H = 1e13; SEG = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "T", "I", "N", "S"]
cov = pd.read_csv(P1 / "bank_coverage_monthly.csv").set_index("year_month")
BANK_DEP_09, BANK_LOAN_09 = cov.loc[140409, "bank_rial_resources"], cov.loc[140409, "bank_loans"]
BANK_DEP_12, BANK_LOAN_12, BANK_NPL_12 = cov.loc[140412, "bank_rial_resources"], cov.loc[140412, "bank_loans"], cov.loc[140412, "bank_npl"]
print("کل رسمی بانک (همت) 09/1404: منابع %.2f وام %.2f | 12/1404: منابع %.2f وام %.2f غیرجاری %.2f" % (BANK_DEP_09 / H, BANK_LOAN_09 / H, BANK_DEP_12 / H, BANK_LOAN_12 / H, BANK_NPL_12 / H))

# ---------- داده‌ی نمونه
dep = pd.read_pickle(D / "customer_month_deposit.pkl", compression=None)
dep = dep[(dep.ym >= 140401) & (dep.ym <= 140409)].copy(); dep["customer_id"] = dep.customer_id.astype("float64").astype("int64")
dep_avg = dep.groupby("customer_id").bal.sum() / 9.0; dep_azar = dep[dep.ym == 140409].groupby("customer_id").bal.sum(); del dep
ln = pd.read_pickle(D / "customer_month_loan_v2.pkl"); ln = ln[(ln.ym >= 140401) & (ln.ym <= 140409)].copy(); ln["customer_id"] = ln.customer_id.astype("float64").astype("int64")
ln["prim"] = ln.bal_primary.fillna(0) + ln.bal_inferred.fillna(0)
loan_avg = ln.groupby("customer_id").prim.sum() / 9.0; loan_azar = ln[ln.ym == 140409].groupby("customer_id").prim.sum(); del ln
F = pd.read_pickle(D / "features_customer_year.pkl"); F = F[F.y == 1404]
seg = pd.read_pickle(D / "cluster_assignments_1404.pkl")[["customer_id", "segment"]]
G = F.merge(seg, on="customer_id"); G["segment"] = G.segment.replace({"O": "I"}); G["province"] = G.province.map(lambda s: norm(s) if isinstance(s, str) else s)
G["dep"] = G.bal_dec.fillna(0); G["loan"] = G.loan_dec_r.fillna(0); G["npl"] = G.npl_dec_r.fillna(0)
G["dep_avg"] = G.customer_id.map(dep_avg).fillna(0); G["dep_azar"] = G.customer_id.map(dep_azar).fillna(0)
G["loan_avg"] = G.customer_id.map(loan_avg).fillna(0); G["loan_azar"] = G.customer_id.map(loan_azar).fillna(0)

# ---------- ۱) آزمون طبقات RFM بانک (09/1404)
RFM = pd.read_excel(ROOT / "data" / "raw" / "phase0_sampling_design" / "RFM.xlsx", sheet_name=None, header=None)
def bands(sheet, last_rows):
    d = RFM[sheet].iloc[2:].copy(); d = d[d[0].notna() | d[2].notna()]
    d = d.iloc[-last_rows:]; return d
dm = RFM["Monetary-Deposite"]; dd = dm.iloc[38:44]; BANK_DEP_BANDS = (dd[2].astype(float) + dd[3].astype(float)).to_numpy()
lm = RFM["Monetary_Loan"]; ll = lm.iloc[39:45]; BANK_LOAN_BANDS = (ll[2].astype(float) + ll[3].astype(float)).to_numpy()
print("طبقات سپرده‌ی بانک:", BANK_DEP_BANDS, "جمع", BANK_DEP_BANDS.sum()); print("طبقات وام بانک:", BANK_LOAN_BANDS, "جمع", BANK_LOAN_BANDS.sum())
DEDGE = np.array([0, 1e7, 5e7, 2e8, 1e9, 5e9, np.inf]); LEDGE = np.array([0, 5e8, 2e9, 1e10, 5e10, 2e11, np.inf])
DL = ["<10م.ر", "10-50م.ر", "50-200م.ر", "200م-1م.ر", "1-5م.ر", ">5م.ر"]; LL = ["<500م.ر", "500م-2م.ر", "2-10م.ر", "10-50م.ر", "50-200م.ر", ">200م.ر"]

Gd = G[G.dep_avg > 0].copy(); Gd["band"] = pd.cut(Gd.dep_avg, DEDGE, right=False, labels=False)
sd = Gd.groupby("band").agg(n=("customer_id", "size"), bal_azar=("dep_azar", "sum")).reindex(range(6)).fillna(0)
sd["bank_n"] = BANK_DEP_BANDS; sd["ratio"] = sd.n / sd.bank_n; sd["w"] = sd.bank_n / sd.n; sd["label"] = DL
sd["implied_azar_hemat"] = sd.w * sd.bal_azar / H
sd.to_csv(D / "s9_deposit_band_test.csv"); print("\nآزمون طبقات سپرده:\n", sd.round(3).to_string())
print("جمع سپرده‌ی نمونه 09/1404 %.2f همت؛ رسمی بانک %.2f همت؛ جمع وزن‌دار با طبقات RFM %.2f همت" % (sd.bal_azar.sum() / H, BANK_DEP_09 / H, sd.implied_azar_hemat.sum()))
n_bad = int((sd.ratio > 1).sum()); print("طبقات با نسبت نمونه به بانک بیش از 1 (غیرممکن):", n_bad, " از 6")

Gl = G[G.loan_avg > 0].copy(); Gl["band"] = pd.cut(Gl.loan_avg, LEDGE, right=False, labels=False)
sl = Gl.groupby("band").agg(n=("customer_id", "size"), loan_azar=("loan_azar", "sum")).reindex(range(6)).fillna(0)
sl["bank_n"] = BANK_LOAN_BANDS; sl["ratio"] = sl.n / sl.bank_n; sl["w"] = sl.bank_n / sl.n; sl["label"] = LL
sl["implied_azar_hemat"] = sl.w * sl.loan_azar / H
sl.to_csv(D / "s9_loan_band_test.csv"); print("\nآزمون طبقات وام:\n", sl.round(3).to_string())
print("جمع وام اصلی نمونه 09/1404 %.2f همت؛ رسمی بانک %.2f؛ جمع وزن‌دار با طبقات RFM %.2f" % (sl.loan_azar.sum() / H, BANK_LOAN_09 / H, sl.implied_azar_hemat.sum()))

# ---------- ۲) وزن استانی (ارزش) از آمار رسمی 12/1404
PO = pd.read_csv(P1 / "province_sample_vs_official_140412.csv", encoding="utf-8-sig"); PO["province"] = PO.province.map(norm); PO = PO.set_index("province")
Ga = G[G.province.notna()]
sp = pd.DataFrame({"dep_s": Ga.groupby("province").dep.sum(), "loan_s": Ga.groupby("province").loan.sum(), "npl_s": Ga.groupby("province").npl.sum()})
KD = G.dep.sum() / Ga.dep.sum(); KL = G.loan.sum() / Ga.loan.sum()   # مشتریان بدون استان به‌تناسب میان استان‌ها فرض می‌شوند
pw = PO.join(sp, how="outer"); pw["w_dep"] = pw.official_resources / (pw.dep_s * KD); pw["w_loan"] = (pw.official_loans / (pw.loan_s * KL)).where(pw.official_loans > 0)
pw.to_csv(D / "s9_province_weights.csv"); print("\nوزن استانی:\n", (pw[["official_resources", "dep_s", "w_dep", "official_loans", "loan_s", "w_loan"]].assign(official_resources=lambda x: x.official_resources / H, dep_s=lambda x: x.dep_s / H, official_loans=lambda x: x.official_loans / H, loan_s=lambda x: x.loan_s / H)).round(2).to_string())
print("جمع رسمی (همت): منابع %.2f وام %.2f؛ جمع نمونه با استان: سپرده %.2f وام %.2f" % (PO.official_resources.sum() / H, PO.official_loans.sum() / H, sp.dep_s.sum() / H, sp.loan_s.sum() / H))

# ---------- وزن‌ها
G["band_val"] = np.where(G.loan_avg > 0, G.loan_avg, G.loan); G["w_band"] = 1.0; m = G.band_val > 0   # وام فقط در پایان سال: طبقه از مانده‌ی 12/1404
G.loc[m, "w_band"] = pd.cut(G.loc[m, "band_val"], LEDGE, right=False, labels=False).map(sl.w).astype(float)
fd_ = pw.w_dep.copy(); mean_fd = PO.official_resources.sum() / G.dep.sum()
G["w_dep_prov"] = G.province.map(fd_).fillna(mean_fd).astype(float)
G["w_loan_prov"] = G.province.map(pw.w_loan).fillna(PO.official_loans.sum() / G.loan.sum()).astype(float)
# raking وام: طبقه (شمار گیرنده‌ی بانک) × استان (مانده‌ی رسمی)
G["w_rake"] = np.where(m, G.w_band, 1.0); bor = G[m].index
band_id = pd.cut(G.loc[bor, "band_val"], LEDGE, right=False, labels=False).astype(int)
for it in range(60):
    tot = pd.Series(G.loc[bor, "w_rake"].to_numpy()).groupby(band_id.to_numpy()).sum().reindex(range(6))
    f = (sl.bank_n / tot).to_numpy(); G.loc[bor, "w_rake"] *= f[band_id.to_numpy()]
    lv = (G.loc[bor, "w_rake"] * G.loc[bor, "loan"]).groupby(G.loc[bor, "province"]).sum()
    fp = (PO.official_loans.where(PO.official_loans > 0) / lv).reindex(lv.index).fillna(1.0); G.loc[bor, "w_rake"] *= G.loc[bor, "province"].map(fp).fillna(1.0).to_numpy()
    ol = PO.official_loans.reindex(lv.index); ok = ol > 0; err = np.nanmax(np.r_[((tot - sl.bank_n).abs() / sl.bank_n).to_numpy(), ((lv - ol).abs() / ol)[ok].to_numpy()])
    if err < 1e-3: break
print("\nraking: تکرار %d، بیشینه خطای نسبی حاشیه‌ها %.4f" % (it + 1, err))
Bm = G.loc[bor]
val = []
for nm, w in [("بدون وزن", np.ones(len(Bm))), ("وزن طبقه‌ی وام", Bm.w_band.to_numpy()), ("وزن استان (وام)", Bm.w_loan_prov.to_numpy()), ("raking طبقه × استان", Bm.w_rake.to_numpy())]:
    wl = (w * Bm.loan.to_numpy()).sum(); wn = (w * Bm.npl.to_numpy()).sum()
    prov_l = (Bm.assign(w=w, wl=lambda x: x.w * x.loan)).groupby("province").wl.sum().reindex(PO.index)
    ok = PO.official_loans > 0; mape = float(((prov_l - PO.official_loans).abs() / PO.official_loans)[ok].mean(skipna=True))
    bw = pd.Series(w).groupby(band_id.to_numpy()).sum().reindex(range(6)).to_numpy(); band_err = float((np.abs(bw - sl.bank_n.to_numpy()) / sl.bank_n.to_numpy()).mean())
    val.append(dict(scheme=nm, borrowers_w=float(w.sum()), loan_hemat_12=wl / H, loan_vs_official=wl / BANK_LOAN_12, npl_hemat_12=wn / H, npl_vs_official=wn / BANK_NPL_12, province_loan_mape=mape, band_count_mape=band_err, max_w=float(w.max()), min_w=float(w.min())))
V = pd.DataFrame(val); V.to_csv(D / "s9_validation.csv", index=False); print("\nاعتبارسنجی وزن‌ها (وام 12/1404؛ رسمی: وام %.2f، غیرجاری %.2f همت، گیرندگان RFM %d):\n" % (BANK_LOAN_12 / H, BANK_NPL_12 / H, BANK_LOAN_BANDS.sum()), V.round(3).to_string())
# سازگاری سپرده با وزن استانی
dw = (G.dep * G.w_dep_prov).sum(); print("سپرده‌ی وزن‌دار استانی %.2f همت؛ رسمی %.2f" % (dw / H, BANK_DEP_12 / H))

# ---------- سهم وزن‌دار خوشه‌ها
def sh(col, w): return (G[col] * w).groupby(G.segment).sum().reindex(SEG) / (G[col] * w).sum() * 100
cnt_b = lambda w: (np.where(m, w, 0)).copy()
Wb = G.w_band.to_numpy(); Wr = G.w_rake.to_numpy(); Wl = G.w_loan_prov.to_numpy(); Wd = G.w_dep_prov.to_numpy(); one = np.ones(len(G))
T = pd.DataFrame({
    "deposit_sample": sh("dep", one), "deposit_province": sh("dep", Wd),
    "loan_sample": sh("loan", one), "loan_province": sh("loan", Wl), "loan_band": sh("loan", Wb), "loan_raked": sh("loan", Wr),
    "npl_sample": sh("npl", one), "npl_province": sh("npl", Wl), "npl_band": sh("npl", Wb), "npl_raked": sh("npl", Wr)})
for nm, w in [("sample", one), ("band", Wb), ("raked", Wr)]:
    b = G[m]; T["borrowers_" + nm] = (pd.Series(w[m.to_numpy()], index=b.index).groupby(b.segment).sum().reindex(SEG) / w[m.to_numpy()].sum() * 100).fillna(0)
T.loc["NPL ratio total"] = np.nan
def ratio(w): return (G.npl * w).groupby(G.segment).sum().reindex(SEG) / (G.loan * w).groupby(G.segment).sum().reindex(SEG) * 100
R = pd.DataFrame({"sample": ratio(one), "band": ratio(Wb), "raked": ratio(Wr)}); R.loc["کل"] = [(G.npl * w).sum() / (G.loan * w).sum() * 100 for w in (one, Wb, Wr)]
T.drop(index="NPL ratio total").to_csv(D / "s9_cluster_shares_weighted.csv"); R.to_csv(D / "s9_npl_ratio_weighted.csv")
pd.set_option("display.width", 250); print("\nسهم خوشه‌ها (٪):\n", T.drop(index="NPL ratio total").round(1).to_string()); print("\nنسبت غیرجاری (٪):\n", R.round(1).to_string())
rg = T.drop(index="NPL ratio total")[["loan_sample", "loan_province", "loan_band", "loan_raked"]]; rg = pd.DataFrame({"min": rg.min(1), "max": rg.max(1)}); rg["range"] = rg["max"] - rg["min"]
rgn = T.drop(index="NPL ratio total")[["npl_sample", "npl_province", "npl_band", "npl_raked"]]; rg["npl_min"] = rgn.min(1); rg["npl_max"] = rgn.max(1); rg.to_csv(D / "s9_share_ranges.csv"); print("\nدامنه‌ی سهم وام و غیرجاری میان وزن‌دهی‌ها:\n", rg.round(1).to_string())

# ---------- نمودارها
fig, axs = plt.subplots(1, 2, figsize=(12, 4.6)); x = np.arange(6)
axs[0].bar(x, sd.ratio.to_numpy(), color=[RED if r > 1 else BLUE for r in sd.ratio], width=.6); axs[0].axhline(1, color=GREY, ls="--"); axs[0].set_yscale("log"); axs[0].set_xticks(x); axs[0].set_xticklabels(DL, rotation=20, ha="right", fontsize=9)
axs[0].set_ylabel("نسبت شمار نمونه به بانک (لگاریتمی)"); axs[0].set_title("طبقات سپرده")
axs[1].bar(x, sl.ratio.to_numpy(), color=[RED if r > 1 else BLUE for r in sl.ratio], width=.6); axs[1].axhline(1, color=GREY, ls="--"); axs[1].set_xticks(x); axs[1].set_xticklabels(LL, rotation=20, ha="right", fontsize=9); axs[1].set_title("طبقات وام")
save(fig, "ch9_band_coverage.png")
fig, axs = plt.subplots(1, 2, figsize=(13, 4.8)); xx = np.arange(len(SEG)); w_ = .2
for ax, pre, title in ((axs[0], "loan", "سهم از مانده‌ی تسهیلات (٪)"), (axs[1], "npl", "سهم از مانده‌ی غیرجاری (٪)")):
    for k, (c, col, lab) in enumerate([("sample", BLUE, "نمونه"), ("province", GREEN, "وزن استان"), ("band", ORANGE, "وزن طبقه‌ی وام"), ("raked", RED, "raking")]):
        ax.bar(xx + (k - 1.5) * w_, T[f"{pre}_{c}"].reindex(SEG), w_, color=col, label=lab)
    ax.set_xticks(xx); ax.set_xticklabels(SEG); ax.set_ylabel(title)
axs[0].legend(frameon=False); save(fig, "ch9_weighted_shares.png")
