"""فاز ۲ - S5b: لنز اعتبار: خوشه‌بندی گیرندگان اصلی تسهیلات (قراردادی و استنتاجی؛ گروه‌های مدل، T و نوپا) بر پایه‌ی ویژگی‌های وام، بازپرداخت، شرایط قرارداد و زمینه‌ی سپرده.
دفتر اقساط با تقویم دقیق جلالی (06b). گمشده‌ی صفات قرارداد/دفتر: میانه + پرچم.
استفاده: python -u 30_s5b_credit_lens.py select   |   python -u 30_s5b_credit_lens.py final K"""
import sys, time
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, roc_auc_score, silhouette_score

MODE = sys.argv[1]; D = Path(__file__).resolve().parents[2] / "data" / "processed" / "phase2_clustering"
SEED = 20261024; t0 = time.time()
def tick(*a): print(f"[{time.time()-t0:6.0f}s]", *a, flush=True)
F = pd.read_pickle(D / "features_customer_year.pkl")
pan = pd.read_pickle(D / "panel_customer_year.pkl")[["customer_id", "y", "bal_max"]]; F = F.merge(pan, on=["customer_id", "y"], how="left")
F["token_borrower"] = (F.category == "model") & F.has_primary_loan & ((F.turn_months < 3) | (F.bal_max < 5e6))

# دفتر اقساط دقیق
lg = pd.read_pickle(D / "customer_month_ledger_exact.pkl"); lg["cid"] = lg.cid.astype("float64").astype("int64"); lg["y"] = (lg.due_ym // 100).astype(np.int16)
lg = lg[(lg.due_ym >= 140001) & (lg.due_ym <= 140412)]
la = lg.groupby(["cid", "y"]).agg(n_inst=("n_inst", "sum"), n_late=("n_late", "sum"), n_late30=("n_late30", "sum"), n_late90=("n_late90", "sum"), sum_dpd=("sum_dpd", "sum"),
                                 s_main=("s_main", "sum"), s_pen=("s_pen", "sum"), n_bad=("n_moaavagh", "sum"), n_mash=("n_mashkoo", "sum")).reset_index().rename(columns={"cid": "customer_id"})
la["late30_x"] = la.n_late30 / la.n_inst; la["late90_x"] = la.n_late90 / la.n_inst; la["mean_dpd_x"] = (la.sum_dpd / la.n_inst).clip(-30, 365)
la["penalty_x"] = (la.s_pen / np.maximum(la.s_main, 1)).clip(0, 1); la["bad_x"] = (la.n_bad + la.n_mash) / la.n_inst
F = F.merge(la[["customer_id", "y", "late30_x", "late90_x", "mean_dpd_x", "penalty_x", "bad_x"]], on=["customer_id", "y"], how="left")
tick("ledger exact merged")

POP = lambda y: F[(F.y == y) & (F.has_loan_dec == 1) & F.category.isin(["model", "newcomer"])].reset_index(drop=True)
A, B = POP(1404), POP(1403)
FEATS = [("loan_log", lambda d: np.log1p(d.loan_dec_r.clip(lower=0)), "exposure"), ("loan_to_dep_log", lambda d: np.log1p(d.loan_to_dep.clip(lower=0)), "exposure"),
         ("n_loan_log", lambda d: np.log1p(d.n_loan_dec), "exposure"), ("loan_months", lambda d: d.loan_months / 12, "exposure"), ("guar_log", lambda d: np.log1p(d.guar_dec_r.clip(lower=0)), "exposure"),
         ("npl_share", lambda d: d.npl_share, "performance"), ("late30", lambda d: d.late30_x, "performance"), ("late90", lambda d: d.late90_x, "performance"),
         ("mean_dpd", lambda d: d.mean_dpd_x, "performance"), ("bad_status", lambda d: d.bad_x, "performance"), ("penalty", lambda d: d.penalty_x, "performance"),
         ("rate", lambda d: d.rate_w, "terms"), ("loan_age", lambda d: d.age_w / 12, "terms"), ("collateral", lambda d: d.coll_w, "terms"), ("duration", lambda d: d.duration_w / 365, "terms"),
         ("t_qard", lambda d: d.ltype_qard, "terms"), ("t_murabaha", lambda d: d.ltype_murabaha, "terms"), ("t_installment", lambda d: d.ltype_installment, "terms"),
         ("s_services", lambda d: d.sector_services, "sector"), ("s_industry", lambda d: d.sector_industry, "sector"), ("s_housing", lambda d: d.sector_housing, "sector"),
         ("s_agri", lambda d: d.sector_agri, "sector"), ("s_trade", lambda d: d.sector_trade, "sector"),
         ("dep_end_log", lambda d: np.log1p(d.bal_end_r.clip(lower=0)), "deposit"), ("dep_trend", lambda d: d.bal_trend, "deposit"), ("dep_turn", lambda d: d.turn_share, "deposit"), ("dep_drawdown", lambda d: d.drawdown, "deposit")]
def raw(d):
    X = pd.DataFrame({n: fn(d).astype(float).to_numpy() for n, fn, _ in FEATS}); X["no_contract_attr"] = d.rate_w.isna().astype(float).to_numpy(); X["no_ledger"] = d.late30_x.isna().astype(float).to_numpy(); return X
RA = raw(A); med = RA.median(); lo, hi = RA.quantile(.005), RA.quantile(.995)
cols = list(RA.columns); blocks = [b for _, _, b in FEATS] + ["flags", "flags"]
cnt = pd.Series(blocks).value_counts(); w = np.array([1 / np.sqrt(cnt[b]) for b in blocks])
bin_cols = {"no_contract_attr", "no_ledger"}
def prep(d):
    X = raw(d).fillna(med); X = X.clip(lo, hi, axis=1)
    mu, sd = RA.fillna(med).clip(lo, hi, axis=1).mean(), RA.fillna(med).clip(lo, hi, axis=1).std().replace(0, 1)
    return ((X - mu) / sd).to_numpy().astype("float32") * w
XA, XB = prep(A), prep(B)
tick("credit population", len(A), len(B), "features", XA.shape[1], " T share:", round(float(A.token_borrower.mean()), 3))

N = F[F.y == 1404].set_index("customer_id"); nxt = N.reindex(B.customer_id.to_numpy()); present = B.customer_id.isin(N.index).to_numpy()
m_npl = (B.npl_share.to_numpy() == 0); y_npl = present & (nxt.npl_share.fillna(0).to_numpy() > 0)
m_late = B.late30_x.notna().to_numpy(); y_late = (nxt.late30_x.fillna(0).to_numpy() > 0.5) & present
OUT = {"npl_entry": (m_npl, y_npl), "late_next": (m_late & (B.late30_x.fillna(0).to_numpy() <= 0.5), y_late)}
def crossfit(lab):
    rs = np.random.default_rng(SEED); half = rs.random(len(lab)) < 0.5; K = lab.max() + 1; res = {}
    for k_, (m_, y_) in OUT.items():
        score = np.full(len(lab), np.nan)
        for h in (True, False):
            tr = m_ & (half == h); te = m_ & (half != h)
            n_c = np.bincount(lab[tr], minlength=K); s_c = np.bincount(lab[tr], weights=y_[tr].astype(float), minlength=K)
            score[te] = np.where(n_c > 0, s_c / np.maximum(n_c, 1), y_[tr].mean())[lab[te]]
        ok = m_ & ~np.isnan(score); res["auc_" + k_] = float(roc_auc_score(y_[ok], score[ok])); res["rate_" + k_] = float(y_[m_].mean())
    return res

if MODE == "select":
    rows = []; SIL = [np.random.default_rng(SEED + i).choice(len(A), 20000, replace=False) for i in range(3)]
    for k in [4, 5, 6, 7, 8]:
        mA = KMeans(k, n_init=30, random_state=SEED).fit(XA); lA = mA.labels_
        mB = KMeans(k, n_init=30, random_state=SEED).fit(XB); lB = mB.labels_; lBA = mB.predict(XA)
        rs = np.random.default_rng(SEED + k); hs = []
        for _ in range(2):
            perm = rs.permutation(len(XA)); h1, h2 = perm[: len(perm) // 2], perm[len(perm) // 2:]
            hs.append(adjusted_rand_score(KMeans(k, n_init=20, random_state=SEED).fit(XA[h1]).predict(XA), KMeans(k, n_init=20, random_state=SEED + 1).fit(XA[h2]).predict(XA)))
        p_ = np.bincount(lA) / len(lA)
        row = dict(k=k, half_ari=float(np.mean(hs)), temporal_ari=adjusted_rand_score(lA, lBA), min_share=float(p_.min()), entropy=float(-(p_ * np.log(p_)).sum() / np.log(k)),
                   sil=float(np.mean([silhouette_score(XA[i], lA[i]) for i in SIL])))
        row.update(crossfit(lB)); rows.append(row); pd.DataFrame(rows).to_csv(D / "s5b_credit_lens_kselect.csv", index=False)
        tick({a: round(b, 3) for a, b in row.items()})
else:
    K = int(sys.argv[2]); km = KMeans(K, n_init=50, random_state=SEED).fit(XA)
    order = np.argsort(-km.cluster_centers_[:, cols.index("loan_log")]); remap = np.empty(K, int); remap[order] = np.arange(K); lab = remap[km.labels_] + 1
    L = pd.DataFrame({"customer_id": A.customer_id, "credit_lens": lab}); L.to_pickle(D / "credit_lens_labels_1404.pkl")
    seg = pd.read_pickle(D / "cluster_assignments_1404.pkl")[["customer_id", "segment"]]; G = A.merge(L, on="customer_id").merge(seg, on="customer_id")
    rows = []
    for c, g in G.groupby("credit_lens"):
        wt = g.loan_dec_r
        rows.append(dict(lens=c, borrowers=len(g), share_borrowers=len(g) / len(G), loan_hemat=g.loan_dec_r.sum() / 1e13, loan_share=g.loan_dec_r.sum() / G.loan_dec_r.sum(),
                         npl_ratio=g.npl_dec_r.sum() / g.loan_dec_r.sum(), npl_share_of_total=g.npl_dec_r.sum() / G.npl_dec_r.sum(), share_with_npl=(g.npl_dec_r > 0).mean(),
                         median_loan_mtoman=g.loan_dec_r.median() / 1e7, median_loan_to_dep=g.loan_to_dep.median(), mean_n_loans=g.n_loan_dec.mean(),
                         late30=g.late30_x.mean(), late90=g.late90_x.mean(), mean_dpd=g.mean_dpd_x.mean(), bad_status=g.bad_x.mean(), ledger_cov=g.late30_x.notna().mean(),
                         rate=np.average(g.rate_w.dropna(), weights=wt[g.rate_w.notna()]) if g.rate_w.notna().any() else np.nan, loan_age_years=g.age_w.mean() / 12, collateral=g.coll_w.mean(),
                         t_qard=g.ltype_qard.mean(), t_murabaha=g.ltype_murabaha.mean(), t_installment=g.ltype_installment.mean(),
                         s_services=g.sector_services.mean(), s_industry=g.sector_industry.mean(), s_housing=g.sector_housing.mean(), s_agri=g.sector_agri.mean(), s_trade=g.sector_trade.mean(),
                         median_dep_mtoman=g.bal_end_r.median() / 1e7, dep_trend=g.bal_trend.mean(), share_token=g.token_borrower.mean(), contract_cov=g.rate_w.notna().mean()))
    P = pd.DataFrame(rows); P.to_csv(D / "s5b_credit_lens_profile.csv", index=False)
    ct = pd.crosstab(G.credit_lens, G.segment); ct.to_csv(D / "s5b_credit_lens_crosstab.csv")
    gt = G[G.segment.str.startswith("C")]; tick("ARI credit lens vs main clusters (borrowers in C1..C8): %.3f" % adjusted_rand_score(gt.credit_lens, gt.segment))
    pd.set_option("display.width", 300); print(P.round(3).T.to_string()); print(ct.to_string())
