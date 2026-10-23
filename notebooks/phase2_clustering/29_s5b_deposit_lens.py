"""فاز ۲ - S5b: لنز سپرده: خوشه‌بندی همه‌ی مشتریان گروه مدل (شامل T) فقط بر پایه‌ی ویژگی‌های سپرده (بلوک‌های اندازه، جریان، فعالیت، ثبات، ساختار).
استفاده: python -u 29_s5b_deposit_lens.py select   |   python -u 29_s5b_deposit_lens.py final K
خروجی: s5b_deposit_lens_kselect.csv، deposit_lens_labels_1404.pkl، s5b_deposit_lens_profile.csv، s5b_deposit_lens_crosstab.csv"""
import sys, time
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, roc_auc_score, silhouette_score
from tt_bank.phase2_clustering.prep import Prep, BLOCKS, NAMES

MODE = sys.argv[1]; D = Path(__file__).resolve().parents[2] / "data" / "processed" / "phase2_clustering"
SEED = 20261023; t0 = time.time()
def tick(*a): print(f"[{time.time()-t0:6.0f}s]", *a, flush=True)
F = pd.read_pickle(D / "features_customer_year.pkl")
pan = pd.read_pickle(D / "panel_customer_year.pkl")[["customer_id", "y", "bal_max"]]; F = F.merge(pan, on=["customer_id", "y"], how="left")
M = F[F.category == "model"]; A = M[M.y == 1404].reset_index(drop=True); B = M[M.y == 1403].reset_index(drop=True)
prep = Prep.from_json(D / "prep_spec_v2.json"); sel = [i for i, b in enumerate(BLOCKS) if b != "loan"]
XA, XB = prep.transform(A)[:, sel], prep.transform(B)[:, sel]
tick("population", len(A), len(B), "features", len(sel))

N = F[F.y == 1404].set_index("customer_id"); nxt = N.reindex(B.customer_id.to_numpy()); present = B.customer_id.isin(N.index).to_numpy()
bal_now, bal_next = B.bal_dec.fillna(0).to_numpy(), nxt.bal_dec.fillna(0).to_numpy()
OUT = {"loan_uptake": (B.has_loan_dec.to_numpy() == 0, (nxt.has_loan_dec.fillna(0).to_numpy() == 1) & present),
       "balance_halved": (bal_now > 0, (~present) | (bal_next < 0.5 * bal_now)),
       "lowactivity_next": (np.ones(len(B), bool), (~present) | (nxt.category.fillna("").to_numpy() == "idle_token") | (nxt.turn_share.fillna(0).to_numpy() < 0.25))}
def crossfit(lab):
    rs = np.random.default_rng(SEED); half = rs.random(len(lab)) < 0.5; K = lab.max() + 1; res = {}
    for k_, (m_, y_) in OUT.items():
        score = np.full(len(lab), np.nan)
        for h in (True, False):
            tr = m_ & (half == h); te = m_ & (half != h)
            n_c = np.bincount(lab[tr], minlength=K); s_c = np.bincount(lab[tr], weights=y_[tr].astype(float), minlength=K)
            score[te] = np.where(n_c > 0, s_c / np.maximum(n_c, 1), y_[tr].mean())[lab[te]]
        ok = m_ & ~np.isnan(score); res["auc_" + k_] = float(roc_auc_score(y_[ok], score[ok]))
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
        row.update(crossfit(lB)); rows.append(row); pd.DataFrame(rows).to_csv(D / "s5b_deposit_lens_kselect.csv", index=False)
        tick({a: round(b, 3) for a, b in row.items()})
else:
    K = int(sys.argv[2]); km = KMeans(K, n_init=50, random_state=SEED).fit(XA)
    order = np.argsort(-km.cluster_centers_[:, [NAMES[i] for i in sel].index("bal_mean_log")]); remap = np.empty(K, int); remap[order] = np.arange(K); lab = remap[km.labels_] + 1
    L = pd.DataFrame({"customer_id": A.customer_id, "deposit_lens": lab}); L.to_pickle(D / "deposit_lens_labels_1404.pkl")
    seg = pd.read_pickle(D / "cluster_assignments_1404.pkl")[["customer_id", "segment"]]
    G = A.merge(L, on="customer_id").merge(seg, on="customer_id")
    rows = []
    for c, g in G.groupby("deposit_lens"):
        b = g[g.has_loan_dec == 1]
        rows.append(dict(lens=c, customers=len(g), share_customers=len(g) / len(G), deposit_share=g.bal_dec.sum() / G.bal_dec.sum(), loan_share=g.loan_dec_r.sum() / G.loan_dec_r.sum(),
                         share_with_loan=(g.has_loan_dec == 1).mean(), median_balance_mtoman=g.bal_mean_r.median() / 1e7, mean_turn_share=g.turn_share.mean(), median_txn=(g.crn_sum + g.dbn_sum).median(),
                         mean_bal_cv=g.bal_cv.mean(), mean_trend=g.bal_trend.mean(), mean_acc=g.acc_mean.mean(), median_tenure_years=g.tenure_months.median() / 12,
                         mean_flow_ratio=g.flow_ratio.mean(), share_type_long=np.average(g.share_long_k, weights=g.bal_end_r + 1), share_type_current=np.average(g.share_current_k, weights=g.bal_end_r + 1)))
    pd.DataFrame(rows).to_csv(D / "s5b_deposit_lens_profile.csv", index=False)
    main = G.segment.where(G.segment.str.startswith("C"), "T")
    ct = pd.crosstab(G.deposit_lens, G.segment); ct.to_csv(D / "s5b_deposit_lens_crosstab.csv")
    cm = G[G.segment.str.startswith("C")]
    tick("ARI deposit lens vs main clusters (C1..C8 customers): %.3f" % adjusted_rand_score(cm.deposit_lens, cm.segment))
    print(pd.DataFrame(rows).round(3).to_string()); print(ct.to_string())
