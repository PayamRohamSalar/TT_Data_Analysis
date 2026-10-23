"""فاز ۲ - S5: مدل نهایی 1404، تخصیص همه‌ی مشتریان، پروفایل، درخت جانشین، جدول عبور و نمودارها (بدون DB).
استفاده: python -u 28_s5_final_model_profile.py K_MAIN K_RFM    مثال: 8 7"""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter, ScalarFormatter
from sklearn.cluster import KMeans
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.metrics import adjusted_rand_score
from tt_bank.common.persian_plot import FONTS_DIR, setup_persian_font, to_persian_digits
from tt_bank.phase2_clustering.prep import Prep, NAMES, BLOCKS

KM_, KR_ = int(sys.argv[1]), int(sys.argv[2])
ROOT = Path(__file__).resolve().parents[2]; D = ROOT / "data" / "processed" / "phase2_clustering"
FIG = ROOT / "reports" / "figures" / "phase2_clustering"; SEED = 20261022
setup_persian_font(); font_manager.fontManager.addfont(str(FONTS_DIR / "Vazirmatn-Bold.ttf"))
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 11, "savefig.dpi": 200, "axes.grid": True, "grid.color": "#E6E6E6", "axes.axisbelow": True})
fd = to_persian_digits; BLUE, ORANGE, GREEN, RED, GREY = "#1F4E79", "#C55A11", "#548235", "#B03A2E", "#7F7F7F"
log = []
def p(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); log.append(s)
def save(fig, name):
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            f = axis.get_major_formatter()
            if isinstance(f, ScalarFormatter): axis.set_major_formatter(FuncFormatter(lambda v, pos: fd(f"{v:g}")))
            elif isinstance(f, FuncFormatter): axis.set_major_formatter(FuncFormatter(lambda v, pos, f=f: fd(f(v, pos))))
    fig.savefig(FIG / name, bbox_inches="tight", facecolor="white"); plt.close(fig); p("saved", name)
FA = {"bal_mean_log": "مانده‌ی میانگین", "bal_end_log": "مانده‌ی پایان سال", "flow_total_log": "گردش کل", "flow_ratio": "سهم گردش بستانکار", "turnover_speed_log": "سرعت گردش",
      "net_flow_ratio": "خالص جریان", "ticket_cr_log": "مبلغ تراکنش بستانکار", "ticket_db_log": "مبلغ تراکنش بدهکار", "crn_log": "تعداد تراکنش بستانکار", "dbn_log": "تعداد تراکنش بدهکار",
      "turn_share": "سهم ماه‌های فعال", "bal_cv": "ضریب تغییرات مانده", "bal_trend": "روند مانده", "drawdown": "افت از بیشینه", "acc_mean_log": "تعداد حساب", "tenure_years": "قدمت",
      "has_loan": "دارای وام", "loan_log": "مانده‌ی وام", "loan_to_dep_log": "وام به سپرده", "npl_share": "سهم غیرجاری", "n_loan_log": "تعداد قرارداد", "loan_months_y": "ماه‌های دارای وام", "guar_log": "مانده‌ی ضمانت"}
BLOCK_FA = {"size": "اندازه", "flow": "جریان", "activity": "فعالیت", "stability": "ثبات", "structure": "ساختار", "loan": "وام"}

# ---------- داده
F = pd.read_pickle(D / "features_customer_year.pkl")
pan = pd.read_pickle(D / "panel_customer_year.pkl")[["customer_id", "y", "bal_max"]]
F = F.merge(pan, on=["customer_id", "y"], how="left")
F["token_borrower"] = (F.category == "model") & F.has_primary_loan & ((F.turn_months < 3) | (F.bal_max < 5e6))
M = F[(F.category == "model") & ~F.token_borrower]; A = M[M.y == 1404].reset_index(drop=True)
prep = Prep.from_json(D / "prep_spec_v2.json"); XA = prep.transform(A)

# ---------- مدل نهایی
km = KMeans(KM_, n_init=50, random_state=SEED).fit(XA)
order = np.argsort(-km.cluster_centers_[:, NAMES.index("bal_mean_log")])      # خوشه‌ها از بزرگ‌ترین مانده‌ی میانگین
remap = np.empty(KM_, int); remap[order] = np.arange(KM_)
lab = remap[km.labels_]; centers = km.cluster_centers_[order]
A["cluster"] = lab + 1
json.dump({"k": KM_, "seed": SEED, "n_init": 50, "features": NAMES, "centers_std": centers.tolist(), "inertia": float(km.inertia_)}, open(D / "s5_final_centers.json", "w"), ensure_ascii=False)
p("final model k=%d inertia %.0f ; sizes:" % (KM_, km.inertia_), np.bincount(lab).tolist())

# ---------- تخصیص همه‌ی مشتریان 1404
Fa = F[F.y == 1404].copy()
Fa["segment"] = "O"
Fa.loc[Fa.category == "institutional_candidate", "segment"] = "S"
Fa.loc[Fa.category == "newcomer", "segment"] = "N"
Fa.loc[Fa.category == "idle_token", "segment"] = "I"
Fa.loc[Fa.token_borrower, "segment"] = "T"
cl = A.set_index("customer_id").cluster
m = Fa.customer_id.isin(cl.index)
Fa.loc[m, "segment"] = "C" + Fa.loc[m, "customer_id"].map(cl).astype(int).astype(str)
Fa["cluster"] = Fa.customer_id.map(cl).fillna(0).astype(int)
Fa[["customer_id", "segment", "cluster", "category", "relationship"]].to_pickle(D / "cluster_assignments_1404.pkl")
Fa[["customer_id", "segment", "cluster", "category", "relationship"]].to_csv(D / "cluster_assignments_1404.csv.gz", index=False, compression="gzip")
p("segment counts:", Fa.segment.value_counts().to_dict())

# ---------- پروفایل
def wavg(g, col, w):
    w_ = g[w]; return float((g[col] * w_).sum() / w_.sum()) if w_.sum() > 0 else np.nan
rows = []
T = lambda x: x / 1e13
for seg, g in Fa.groupby("segment"):
    b = g[g.has_loan_dec == 1]
    row = dict(segment=seg, customers=len(g), share_customers=len(g) / len(Fa),
               deposit_hemat=T(g.bal_dec.sum()), share_deposit=g.bal_dec.sum() / Fa.bal_dec.sum(),
               loan_hemat=T(g.loan_dec_r.sum()), share_loan=g.loan_dec_r.sum() / Fa.loan_dec_r.sum(),
               npl_hemat=T(g.npl_dec_r.sum()), npl_ratio=g.npl_dec_r.sum() / g.loan_dec_r.sum() if g.loan_dec_r.sum() > 0 else np.nan,
               share_with_loan=(g.has_loan_dec == 1).mean(), share_primary_record=(g.relationship == "primary_record").mean(),
               share_primary_inferred=(g.relationship == "primary_inferred").mean(), share_party_only=(g.relationship == "party_only").mean(), share_deposit_only=(g.relationship == "deposit_only").mean(),
               median_bal_mean_mtoman=g.bal_mean_r.median() / 1e7, median_bal_end_mtoman=g.bal_end_r.median() / 1e7,
               median_flow_total_mtoman=(g.cr_sum_r + g.db_sum_r).median() / 1e7, median_txn=(g.crn_sum + g.dbn_sum).median(), mean_turn_share=g.turn_share.mean(),
               mean_acc=g.acc_mean.mean(), median_tenure_years=g.tenure_months.median() / 12, mean_bal_cv=g.bal_cv.mean(), mean_trend=g.bal_trend.mean(),
               median_loan_mtoman=b.loan_dec_r.median() / 1e7 if len(b) else np.nan, median_loan_to_dep=b.loan_to_dep.median() if len(b) else np.nan,
               mean_npl_share_borrowers=b.npl_share.mean() if len(b) else np.nan, share_borrowers_with_npl=(b.npl_dec_r > 0).mean() if len(b) else np.nan,
               mean_n_loans=b.n_loan_dec.mean() if len(b) else np.nan,
               share_type_long=wavg(g, "share_long_k", "bal_end_r"), share_type_short=wavg(g, "share_short_k", "bal_end_r"), share_type_qard=wavg(g, "share_qard_k", "bal_end_r"),
               share_type_current=wavg(g, "share_current_k", "bal_end_r"), share_type_special=wavg(g, "share_special_k", "bal_end_r"), mean_unknown_type=wavg(g, "share_unknown", "bal_end_r"),
               share_interest=g.has_interest.mean(), share_fee2385=(g.fee_2385 > 0).mean() if "fee_2385" in g else np.nan, share_fee6157=(g.fee_6157 > 0).mean() if "fee_6157" in g else np.nan,
               share_blocked=g.has_blocked_account.mean(), late30=b.late30_share.mean() if len(b) else np.nan, bad_status=b.bad_status_share.mean() if len(b) else np.nan,
               mean_rate=wavg(b[b.rate_w.notna()], "rate_w", "loan_dec_r") if b.rate_w.notna().any() else np.nan,
               share_ltype_qard=wavg(b[b.ltype_qard.notna()], "ltype_qard", "loan_dec_r") if b.ltype_qard.notna().any() else np.nan,
               share_ltype_murabaha=wavg(b[b.ltype_murabaha.notna()], "ltype_murabaha", "loan_dec_r") if b.ltype_murabaha.notna().any() else np.nan,
               share_ltype_installment=wavg(b[b.ltype_installment.notna()], "ltype_installment", "loan_dec_r") if b.ltype_installment.notna().any() else np.nan)
    pv = g.province.value_counts(normalize=True)
    row.update(top_province=pv.index[0] if len(pv) else "", top_province_share=float(pv.iloc[0]) if len(pv) else np.nan, province_coverage=g.province.notna().mean())
    rows.append(row)
P = pd.DataFrame(rows).set_index("segment")
P = P.loc[[s for s in ["C%d" % i for i in range(1, KM_ + 1)] + ["T", "I", "N", "S", "O"] if s in P.index]]
P.to_csv(D / "cluster_profiles_1404.csv", encoding="utf-8-sig")
pd.set_option("display.width", 250); p(P[["customers", "share_customers", "deposit_hemat", "share_deposit", "loan_hemat", "share_loan", "npl_ratio", "share_with_loan", "median_bal_mean_mtoman", "mean_turn_share", "mean_acc"]].round(3).to_string())

# ---------- درخت جانشین (ویژگی‌های خوانا)
Xr = pd.DataFrame({"bal_mean_mtoman": A.bal_mean_r / 1e7, "bal_end_mtoman": A.bal_end_r / 1e7, "flow_total_mtoman": (A.cr_sum_r + A.db_sum_r) / 1e7,
                   "txn_count": A.crn_sum + A.dbn_sum, "turn_share": A.turn_share, "flow_ratio": A.flow_ratio, "bal_cv": A.bal_cv, "bal_trend": A.bal_trend, "drawdown": A.drawdown,
                   "acc_mean": A.acc_mean, "tenure_years": A.tenure_months / 12, "has_loan": A.has_loan_dec, "loan_mtoman": A.loan_dec_r / 1e7, "loan_to_dep": A.loan_to_dep,
                   "npl_share": A.npl_share, "n_loans": A.n_loan_dec, "guar_mtoman": A.guar_dec_r / 1e7})
rs = np.random.default_rng(SEED); idx = rs.permutation(len(Xr)); tr, te = idx[: int(.6 * len(idx))], idx[int(.6 * len(idx)):]
tree = DecisionTreeClassifier(max_depth=4, random_state=SEED).fit(Xr.iloc[tr], lab[tr])
fid = float((tree.predict(Xr.iloc[te]) == lab[te]).mean()); p("surrogate tree depth 4 fidelity on holdout: %.3f" % fid)
(D / "s5_surrogate_tree_rules.txt").write_text(f"fidelity={fid:.4f}\n" + export_text(tree, feature_names=list(Xr.columns), max_depth=4), encoding="utf-8")

# ---------- جدول عبور با M1 و M2
rfm = pd.read_pickle(D / "rfm_scores.pkl"); R = A[["customer_id", "y"]].merge(rfm[["customer_id", "y", "R", "F", "M", "L", "M_q", "F_q"]], on=["customer_id", "y"], how="left")
Mq, Fq, L_ = R.M_q.to_numpy(), R.F_q.to_numpy(), R.L.to_numpy()
m1 = np.full(len(R), 6); done = np.zeros(len(R), bool)
for i, c in enumerate([(Mq == 5) & (Fq >= 4), (Mq >= 4) & (Fq >= 3), (L_ > 0) & (Fq >= 3), (L_ > 0) & (Fq < 3), (Mq >= 3) & (Fq < 3), (Mq <= 2) & (Fq >= 3)]):
    mm = c & ~done; m1[mm] = i; done |= mm
RFMA = np.column_stack([R.R, R.F, R.M, R.L, A.has_loan_dec]).astype("float32")
km2 = KMeans(KR_, n_init=50, random_state=SEED).fit(RFMA); l2 = km2.labels_
o2 = np.argsort(-km2.cluster_centers_[:, 2]); r2 = np.empty(KR_, int); r2[o2] = np.arange(KR_); l2 = r2[l2]
p("ARI main vs M1: %.3f ; main vs M2(k=%d): %.3f ; M1 vs M2: %.3f" % (adjusted_rand_score(lab, m1), KR_, adjusted_rand_score(lab, l2), adjusted_rand_score(m1, l2)))
pd.crosstab(pd.Series(lab + 1, name="cluster"), pd.Series(m1 + 1, name="M1_segment")).to_csv(D / "s5_crosstab_main_vs_M1.csv")
pd.crosstab(pd.Series(lab + 1, name="cluster"), pd.Series(l2 + 1, name="M2_cluster")).to_csv(D / "s5_crosstab_main_vs_M2.csv")
pd.DataFrame({"customer_id": A.customer_id, "m1": m1 + 1, "m2": l2 + 1}).to_pickle(D / "rfm_lens_labels_1404.pkl")

# ---------- نمودارها
seg_lab = {s: ("خوشه " + fd(s[1:])) if s.startswith("C") else {"T": "وام‌گیر با سپرده‌ی خدماتی", "I": "بی‌فعالیت", "N": "نوپا", "S": "نهادی", "O": "سایر"}[s] for s in P.index}
fig, ax = plt.subplots(figsize=(11.5, 5)); x = np.arange(len(P)); w = .27
ax.bar(x - w, P.share_customers * 100, w, color=BLUE, label="سهم مشتریان"); ax.bar(x, P.share_deposit * 100, w, color=ORANGE, label="سهم مانده‌ی سپرده"); ax.bar(x + w, P.share_loan * 100, w, color=GREEN, label="سهم مانده‌ی تسهیلات")
ax.set_xticks(x); ax.set_xticklabels([seg_lab[s] for s in P.index], rotation=30, ha="right", fontsize=9.5); ax.set_ylabel("درصد"); ax.legend(frameon=False); ax.grid(axis="x", visible=False)
save(fig, "ch5_segment_shares.png")
Z = pd.DataFrame(centers, columns=NAMES)
fig, ax = plt.subplots(figsize=(10, 8.5)); im = ax.imshow(Z.T.values, cmap="RdBu_r", vmin=-2.5, vmax=2.5, aspect="auto"); ax.grid(False)
ax.set_yticks(range(len(NAMES))); ax.set_yticklabels([FA[n] for n in NAMES], fontsize=9); ax.set_xticks(range(KM_)); ax.set_xticklabels([fd(i + 1) for i in range(KM_)]); ax.set_xlabel("خوشه")
for i in range(len(NAMES)):
    for j in range(KM_): ax.text(j, i, fd(f"{Z.values[j, i]:.1f}"), ha="center", va="center", fontsize=7.5, color="white" if abs(Z.values[j, i]) > 1.4 else "black")
fig.colorbar(im, shrink=.7); save(fig, "ch5_cluster_heatmap.png")
blk = pd.DataFrame({b: Z[[n for n, bb in zip(NAMES, BLOCKS) if bb == b]].abs().mean(axis=1) * np.sign(Z[[n for n, bb in zip(NAMES, BLOCKS) if bb == b]].mean(axis=1)) for b in BLOCK_FA})
ang = np.linspace(0, 2 * np.pi, len(BLOCK_FA), endpoint=False); ang = np.r_[ang, ang[0]]
nc = 4; nr = int(np.ceil(KM_ / nc)); fig, axes = plt.subplots(nr, nc, figsize=(3.4 * nc, 3.4 * nr), subplot_kw=dict(polar=True))
for i, ax in enumerate(axes.ravel()):
    if i >= KM_: ax.axis("off"); continue
    v = blk.iloc[i].values; ax.plot(ang, np.r_[v, v[0]], color=BLUE, lw=2); ax.fill(ang, np.r_[v, v[0]], color=BLUE, alpha=.2)
    ax.set_xticks(ang[:-1]); ax.set_xticklabels(list(BLOCK_FA.values()), fontsize=8); ax.set_yticks([-1, 0, 1]); ax.set_yticklabels(["", "", ""]); ax.set_ylim(-1.8, 1.8); ax.set_title("خوشه " + fd(i + 1), fontsize=11)
save(fig, "ch5_cluster_radar.png")
fig, ax = plt.subplots(figsize=(10.5, 4.8)); lm = []
for c in range(1, KM_ + 1):
    g = A[A.cluster == c]; lm.append(np.log10(g.bal_mean_r.clip(lower=1) / 1e1))
ax.boxplot(lm, showfliers=False, patch_artist=True, boxprops=dict(facecolor="#9DB7D5"), medianprops=dict(color=RED)); ax.set_xticklabels([fd(i) for i in range(1, KM_ + 1)])
ax.set_ylabel("لگاریتم مانده‌ی میانگین (ریال، log10)"); ax.set_xlabel("خوشه"); save(fig, "ch5_balance_by_cluster.png")
cols = ["share_type_long", "share_type_short", "share_type_qard", "share_type_current", "share_type_special", "mean_unknown_type"]; labs = ["بلندمدت", "کوتاه‌مدت", "قرض‌الحسنه", "جاری", "ویژه", "بدون نوع"]
fig, ax = plt.subplots(figsize=(11, 4.8)); bt = np.zeros(len(P)); cc = ["#1F4E79", "#9DB7D5", "#548235", "#C55A11", "#B8A000", "#BBBBBB"]
Pm = P.loc[[s for s in P.index if s.startswith("C")]]
for c_, l_, col in zip(cols, labs, cc):
    ax.bar(range(len(Pm)), Pm[c_] * 100, bottom=bt[:len(Pm)], color=col, label=l_); bt[:len(Pm)] += (Pm[c_] * 100).values
ax.set_xticks(range(len(Pm))); ax.set_xticklabels([fd(s[1:]) for s in Pm.index]); ax.set_xlabel("خوشه"); ax.set_ylabel("سهم از مانده (درصد)"); ax.legend(frameon=False, ncol=6, fontsize=9, loc="upper center", bbox_to_anchor=(.5, 1.12))
save(fig, "ch5_account_type_mix.png")
(D / "s5_profile_log.txt").write_text("\n".join(log), encoding="utf-8")
