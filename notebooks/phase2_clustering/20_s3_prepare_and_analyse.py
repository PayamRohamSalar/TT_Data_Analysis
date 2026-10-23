"""فاز ۲ - S3: توزیع‌ها، تبدیل، پرت‌ها، بخش نهادی، RFM گسترش‌یافته و نمودارهای فصل ۳ و ۴-۱۱ (بدون DB)."""
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter
from scipy.stats import skew
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, silhouette_score
from tt_bank.common.persian_plot import FONTS_DIR, setup_persian_font, to_persian_digits
from tt_bank.phase2_clustering.prep import Prep, NAMES, BLOCKS, raw_transform

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data" / "processed" / "phase2_clustering"
FIG = ROOT / "reports" / "figures" / "phase2_clustering"; FIG.mkdir(parents=True, exist_ok=True)
setup_persian_font(); font_manager.fontManager.addfont(str(FONTS_DIR / "Vazirmatn-Bold.ttf"))
BLUE, ORANGE, GREEN, RED, GREY = "#1F4E79", "#C55A11", "#548235", "#B03A2E", "#7F7F7F"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 11, "savefig.dpi": 200, "axes.grid": True,
                     "grid.color": "#E6E6E6", "axes.axisbelow": True})
fd = to_persian_digits
log = []
def p(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); log.append(s)
def save(fig, name):
    from matplotlib.ticker import ScalarFormatter
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            f = axis.get_major_formatter()
            if isinstance(f, ScalarFormatter):
                axis.set_major_formatter(FuncFormatter(lambda v, pos: fd(f"{v:g}")))
            elif isinstance(f, FuncFormatter):
                axis.set_major_formatter(FuncFormatter(lambda v, pos, f=f: fd(f(v, pos))))
    fig.savefig(FIG / name, bbox_inches="tight", facecolor="white"); plt.close(fig); p("saved", name)

FA = {"bal_mean_log": "مانده‌ی میانگین", "bal_end_log": "مانده‌ی پایان سال", "flow_total_log": "گردش کل", "flow_ratio": "سهم گردش بستانکار",
      "turnover_speed_log": "سرعت گردش", "net_flow_ratio": "خالص جریان", "ticket_cr_log": "مبلغ تراکنش بستانکار", "ticket_db_log": "مبلغ تراکنش بدهکار",
      "crn_log": "تعداد تراکنش بستانکار", "dbn_log": "تعداد تراکنش بدهکار", "turn_share": "سهم ماه‌های فعال", "recency_y": "ماه‌های بی‌فعالیتی پایان سال",
      "bal_cv": "ضریب تغییرات مانده", "bal_trend": "روند مانده", "drawdown": "افت از بیشینه", "acc_mean_log": "تعداد حساب", "acc_change_slog": "تغییر تعداد حساب",
      "tenure_years": "قدمت", "has_loan": "دارای وام", "loan_log": "مانده‌ی وام", "loan_to_dep_log": "وام به سپرده", "npl_share": "سهم غیرجاری",
      "n_loan_log": "تعداد قرارداد", "loan_months_y": "ماه‌های دارای وام", "guar_log": "مانده‌ی ضمانت"}

F = pd.read_pickle(D / "features_customer_year.pkl")
M = F[F.category == "model"]
ref = M[M.y == 1404]
prep = Prep().fit(ref, panel=M); prep.to_json(D / "prep_spec.json")
p("reference rows", len(ref), "features", len(NAMES))

# ---------- ۱. اثر تبدیل بر چولگی
R = raw_transform(ref)
raw_cols = {"bal_mean_log": ref.bal_mean_r, "bal_end_log": ref.bal_end_r, "flow_total_log": ref.cr_sum_r + ref.db_sum_r, "ticket_cr_log": ref.ticket_cr_r,
            "crn_log": ref.crn_sum, "dbn_log": ref.dbn_sum, "loan_log": ref.loan_dec_r, "guar_log": ref.guar_dec_r, "acc_mean_log": ref.acc_mean}
rows = []
for n in NAMES:
    x = R[n]; xc = x.clip(prep.lo[n], prep.hi[n])
    rows.append(dict(feature=n, block=BLOCKS[NAMES.index(n)], zero_share=float((x == 0).mean()),
                     skew_raw=float(skew(raw_cols[n])) if n in raw_cols else np.nan, skew_transformed=float(skew(x)), skew_winsorized=float(skew(xc))))
sk = pd.DataFrame(rows); sk.to_csv(D / "s3_skew_effect.csv", index=False); p(sk.round(2).to_string())

# ---------- ۲. PCA
X = prep.transform(ref)
pca = PCA().fit(X); cum = pca.explained_variance_ratio_.cumsum()
p("PCA comps for 80/90/95%% variance: %d / %d / %d" % tuple(int(np.searchsorted(cum, v) + 1) for v in (.8, .9, .95)), " first 5:", np.round(pca.explained_variance_ratio_[:5], 3))
fig, ax = plt.subplots(figsize=(7.2, 4.2))
ax.plot(range(1, len(cum) + 1), cum * 100, color=BLUE, marker="o"); ax.axhline(90, color=GREY, ls="--", lw=1)
ax.set_xlabel("تعداد مؤلفه‌ها"); ax.set_ylabel("واریانس تجمعی (درصد)"); save(fig, "ch3_pca_scree.png")

# ---------- ۳. حساسیت: وینزورایز، وزن بلوک، افزودن نهادی
def km(X_, k=8, seed=0):
    return KMeans(k, n_init=3, random_state=seed).fit(X_)
base = km(X); lab = base.labels_
p("base kmeans k=8 sizes:", np.bincount(lab).tolist(), " silhouette(20k): %.3f" % silhouette_score(X[np.random.default_rng(0).choice(len(X), 20000, replace=False)], lab[np.random.default_rng(0).choice(len(X), 20000, replace=False)]))
X_nw = prep.transform(ref, winsorize=False); l2 = km(X_nw).labels_
prep_nb = Prep().fit(ref, block_weights=False, panel=M); l3 = km(prep_nb.transform(ref)).labels_
l4 = km(X, seed=1).labels_
p("ARI base vs no-winsorize: %.3f ; vs no-block-weights: %.3f ; vs other seed: %.3f" % (adjusted_rand_score(lab, l2), adjusted_rand_score(lab, l3), adjusted_rand_score(lab, l4)))
inst = F[(F.y == 1404) & (F.category == "institutional_candidate")]
Xi = prep.transform(inst); li = base.predict(Xi)
p("institutional (574) placed into base clusters:", np.bincount(li, minlength=8).tolist())
Xall = np.vstack([X, Xi]); lall = km(Xall).labels_
p("ARI on shared customers, with vs without institutional in training: %.3f" % adjusted_rand_score(lab, lall[:len(X)]))
dist_inst = np.sqrt(((Xi[:, None, :] - base.cluster_centers_[None, :, :]) ** 2).sum(-1)).min(1)
dist_ref = np.sqrt(((X[:5000][:, None, :] - base.cluster_centers_[None, :, :]) ** 2).sum(-1)).min(1)
p("distance to nearest centre: institutional median %.2f p90 %.2f ; model median %.2f p90 %.2f" % (np.median(dist_inst), np.quantile(dist_inst, .9), np.median(dist_ref), np.quantile(dist_ref, .9)))

# ---------- ۴. بخش نهادی در طول سال‌ها
rows = []
for y, g in F.groupby("y"):
    t = g[g.category == "institutional_candidate"]
    topnon = g[g.category != "institutional_candidate"].nlargest(len(t), "bal_mean_r")
    rows.append(dict(year=y, customers=len(t), share_customers=len(t) / len(g), share_balance=t.bal_mean_r.sum() / g.bal_mean_r.sum(),
                     share_flow=(t.cr_sum_r + t.db_sum_r).sum() / (g.cr_sum_r + g.db_sum_r).sum(), median_accounts=t.acc_mean.median(),
                     share_with_loan=(t.has_loan_dec > 0).mean(), loan_share=t.loan_dec_r.sum() / g.loan_dec_r.sum(),
                     median_balance_hemat_per_cust=t.bal_mean_r.median() / 1e9,
                     comparable_top_noninst_median_balance=topnon.bal_mean_r.median() / 1e9))
it = pd.DataFrame(rows); it.to_csv(D / "s3_institutional_by_year.csv", index=False); p(it.round(4).to_string())

# ---------- ۵. RFM گسترش‌یافته
G = F[["customer_id", "y", "category", "recency", "max_gap", "turn_share", "crn_sum", "dbn_sum", "bal_mean_r", "cr_sum_r", "db_sum_r", "loan_dec_r"]].copy()
prev = G[["customer_id", "y", "turn_share"]].assign(y=lambda d: d.y + 1).rename(columns={"turn_share": "turn_prev"})
G = G.merge(prev, on=["customer_id", "y"], how="left"); G["turn_24"] = (G.turn_share + G.turn_prev.fillna(G.turn_share)) / 2
G["R"] = 1 - np.minimum(np.maximum(G.recency, G.max_gap), 12) / 12
rk = lambda s: s.groupby(G.y).rank(pct=True)
G["F"] = (rk(G.turn_share) + rk(np.log1p(G.crn_sum + G.dbn_sum)) + rk(G.turn_24)) / 3
G["M"] = (rk(np.log1p(G.bal_mean_r)) + rk(np.log1p(G.cr_sum_r + G.db_sum_r))) / 2
G["L"] = np.where(G.loan_dec_r > 0, G.groupby("y").loan_dec_r.rank(pct=True), 0.0)
for c in "RFML":
    G[c + "_q"] = pd.qcut(G[c].rank(method="first"), 5, labels=False) + 1
G.to_pickle(D / "rfm_scores.pkl")
g = G[(G.y == 1404) & (G.category == "model")]
p("RFM 1404 model: unique R values", g.R.nunique(), " R==1 share %.3f ; F deciles:" % (g.R == 1).mean(), g.F.quantile([.1, .5, .9]).round(2).to_dict())
p("quintile score vs rank correlation (Spearman) among M,F:", round(g[["M", "F"]].corr(method="spearman").iloc[0, 1], 3))

# ---------- ۶. نمودارها
# ن ۳-۱: توزیع پیش و پس از تبدیل
trip = [("میانگین مانده‌ی سال (میلیون تومان)", ref.bal_mean_r / 1e7, "bal_mean_log"), ("گردش بستانکار سال (میلیون تومان)", ref.cr_sum_r / 1e7, None),
        ("تعداد تراکنش بستانکار", ref.crn_sum, "crn_log")]
fig, axes = plt.subplots(3, 2, figsize=(10.5, 9))
for i, (title, x, nm) in enumerate(trip):
    x = x.clip(lower=0); hi = x.quantile(.99)
    axes[i, 0].hist(x[x <= hi], bins=60, color=BLUE); axes[i, 0].set_title(title + " (خام، تا صدک ۹۹)", fontsize=10.5)
    axes[i, 1].hist(np.log10(x + 1), bins=60, color=ORANGE); axes[i, 1].set_title("همان متغیر در مقیاس لگاریتمی (log10)", fontsize=10.5)
    axes[i, 0].set_ylabel("تعداد مشتری")
save(fig, "ch3_distribution_before_after_log.png")
# ن ۳-۲: همبستگی
S = prep.transform(ref.sample(100000, random_state=0))
cmat = pd.DataFrame(S, columns=NAMES).corr(method="spearman").values
fig, ax = plt.subplots(figsize=(10.5, 9))
im = ax.imshow(cmat, cmap="RdBu_r", vmin=-1, vmax=1); ax.grid(False)
ax.set_xticks(range(len(NAMES))); ax.set_yticks(range(len(NAMES)))
ax.set_xticklabels([FA[n] for n in NAMES], rotation=90, fontsize=8.5); ax.set_yticklabels([FA[n] for n in NAMES], fontsize=8.5)
fig.colorbar(im, shrink=.7); save(fig, "ch3_feature_correlation.png")
# ن ۳-۳: لورنز و سهم گروه‌ها (۱۴۰۴)
a = F[F.y == 1404].sort_values("bal_mean_r")
cumb = a.bal_mean_r.cumsum() / a.bal_mean_r.sum(); cumc = np.arange(1, len(a) + 1) / len(a)
fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
axes[0].plot(cumc * 100, cumb * 100, color=BLUE, lw=2); axes[0].plot([0, 100], [0, 100], color=GREY, ls="--", lw=1)
axes[0].set_xlabel("سهم تجمعی مشتریان (درصد)"); axes[0].set_ylabel("سهم تجمعی مانده‌ی میانگین (درصد)")
cats = [("model", "قابل خوشه‌بندی"), ("idle_token", "بی‌فعالیت یا نمادین"), ("newcomer", "نوپا"), ("institutional_candidate", "نهادی")]
sc = [(a.category == c).mean() * 100 for c, _ in cats]; sb = [a.bal_mean_r[a.category == c].sum() / a.bal_mean_r.sum() * 100 for c, _ in cats]
x = np.arange(len(cats)); axes[1].bar(x - .2, sc, .38, color=BLUE, label="سهم مشتریان"); axes[1].bar(x + .2, sb, .38, color=ORANGE, label="سهم مانده")
axes[1].set_xticks(x); axes[1].set_xticklabels([c[1] for c in cats], fontsize=9.5); axes[1].legend(frameon=False); axes[1].set_ylabel("درصد"); axes[1].grid(axis="x", visible=False)
for xi, v in zip(x - .2, sc): axes[1].text(xi, v + 1, fd(f"{v:.1f}"), ha="center", fontsize=9)
for xi, v in zip(x + .2, sb): axes[1].text(xi, v + 1, fd(f"{v:.1f}"), ha="center", fontsize=9)
save(fig, "ch3_concentration_lorenz_groups.png")
# ن ۳-۴: فصلی بودن گردش
cm = pd.read_pickle(D / "customer_month_deposit.pkl", )[["ym", "cr"]]
cm = cm[cm.ym >= 140001]; mo = cm.groupby(cm.ym).cr.sum().reset_index(); mo["y"] = mo.ym // 100; mo["m"] = mo.ym % 100
mo["share"] = mo.cr / mo.groupby("y").cr.transform("sum") * 100
fig, ax = plt.subplots(figsize=(9, 4.4))
for y, g_ in mo.groupby("y"): ax.plot(g_.m, g_.share, marker="o", lw=1.8, label=fd(y))
ax.set_xticks(range(1, 13)); ax.set_xlabel("ماه سال"); ax.set_ylabel("سهم از گردش بستانکار سال (درصد)"); ax.legend(frameon=False, ncol=5, fontsize=9)
save(fig, "ch3_seasonality.png"); p("month-of-year credit share (avg):", mo.groupby("m").share.mean().round(1).to_dict())
# ن ۳-۵: اثر تورم
cp = pd.read_csv(D / "cpi_monthly_used.csv", index_col=0).cpi
med = M.groupby("y").agg(nominal=("bal_dec", "median"), real=("bal_end_r", "median"))
cd = pd.Series({y: cp.loc[y * 100 + 12] / cp.loc[140012] for y in range(1400, 1405)})
fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
axes[0].plot(med.index, med.nominal / 1e6, color=ORANGE, marker="o", lw=2, label="اسمی"); axes[0].plot(med.index, med.real / 1e6, color=BLUE, marker="o", lw=2, label="به قیمت ثابت ۱۲/۱۴۰۴")
axes[0].set_ylabel("میانه‌ی مانده‌ی پایان سال (میلیون ریال)"); axes[0].legend(frameon=False); axes[0].set_xticks(med.index)
axes[1].bar(cd.index, cd.values, color=GREY); axes[1].set_ylabel("نمایه‌ی قیمت پایان سال (۱۲/۱۴۰۰ برابر ۱)"); axes[1].set_xticks(cd.index); axes[1].grid(axis="x", visible=False)
save(fig, "ch3_inflation_effect.png"); p("median nominal vs real Dec balance:\n" + med.round(0).to_string())
# ن ۴-۱۱: R F M L
fig, axes = plt.subplots(1, 4, figsize=(12.5, 3.6))
for ax, (c, t) in zip(axes, [("R", "تازگی گسترش‌یافته"), ("F", "تکرار گسترش‌یافته"), ("M", "ارزش پولی"), ("L", "وام")]):
    ax.hist(g[c][g[c] > 0] if c == "L" else g[c], bins=40, color=BLUE); ax.set_title(t, fontsize=11)
axes[0].set_ylabel("تعداد مشتری"); save(fig, "ch4_rfm_distributions.png")
(D / "s3_summary.txt").write_text("\n".join(log), encoding="utf-8")
