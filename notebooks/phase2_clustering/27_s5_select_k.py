"""فاز ۲ - S5: انتخاب k برای خوشه‌بندی اصلی روی جمعیت مدل بدون وام‌گیران با سپرده‌ی خدماتی (D15) با سالانه‌سازی (نسخه‌ی 2 تبدیل).
K-Means با n_init=30 و بذر ثابت؛ پایداری نیم‌نمونه و زمانی؛ AUC و lift بیرونی با برازش متقاطع؛ معیارهای داخلی؛ دید RFM-L (M2) برای مقایسه.
خروجی: s5_kselect.csv، prep_spec_v2.json، s5_population.csv (شمار)"""
import time
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, roc_auc_score, silhouette_score, calinski_harabasz_score, davies_bouldin_score
from tt_bank.phase2_clustering.prep import Prep

D = Path(__file__).resolve().parents[2] / "data" / "processed" / "phase2_clustering"; LAB = D / "s5_labels"; LAB.mkdir(exist_ok=True)
SEED = 20261022; t0 = time.time()
def tick(*a): print(f"[{time.time()-t0:6.0f}s]", *a, flush=True)

F = pd.read_pickle(D / "features_customer_year.pkl")
pan = pd.read_pickle(D / "panel_customer_year.pkl")[["customer_id", "y", "bal_max"]]
F = F.merge(pan, on=["customer_id", "y"], how="left")
F["token_borrower"] = (F.category == "model") & F.has_primary_loan & ((F.turn_months < 3) | (F.bal_max < 5e6))
M = F[(F.category == "model") & ~F.token_borrower]
A = M[M.y == 1404].reset_index(drop=True); B = M[M.y == 1403].reset_index(drop=True)
pd.DataFrame([dict(year=y, model_all=int(((F.y == y) & (F.category == "model")).sum()), token_borrowers=int(((F.y == y) & F.token_borrower).sum()),
                   main_population=int((M.y == y).sum())) for y in range(1400, 1405)]).to_csv(D / "s5_population.csv", index=False)
tick("population A", len(A), "B", len(B))
prep = Prep(annualize=True).fit(A, panel=M); prep.to_json(D / "prep_spec_v2.json")
XA, XB = prep.transform(A), prep.transform(B)

rfm = pd.read_pickle(D / "rfm_scores.pkl")
def rf(df): return df[["customer_id", "y"]].merge(rfm[["customer_id", "y", "R", "F", "M", "L"]], on=["customer_id", "y"], how="left")
RA, RB = rf(A), rf(B)
RFMA = np.column_stack([RA.R, RA.F, RA.M, RA.L, A.has_loan_dec.to_numpy()]).astype("float32")
RFMB = np.column_stack([RB.R, RB.F, RB.M, RB.L, B.has_loan_dec.to_numpy()]).astype("float32")

N = F[F.y == 1404].set_index("customer_id"); nxt = N.reindex(B.customer_id.to_numpy()); present = B.customer_id.isin(N.index).to_numpy()
bal_now, bal_next = B.bal_dec.fillna(0).to_numpy(), nxt.bal_dec.fillna(0).to_numpy()
OUT = {"loan_uptake": (B.has_loan_dec.to_numpy() == 0, (nxt.has_loan_dec.fillna(0).to_numpy() == 1) & present),
       "balance_halved": (bal_now > 0, (~present) | (bal_next < 0.5 * bal_now)),
       "lowactivity_next": (np.ones(len(B), bool), (~present) | (nxt.category.fillna("").to_numpy() == "idle_token") | (nxt.turn_share.fillna(0).to_numpy() < 0.25)),
       "npl_entry": ((B.has_loan_dec.to_numpy() == 1) & (B.npl_share.to_numpy() == 0), present & (nxt.npl_share.fillna(0).to_numpy() > 0))}
for k_, (m_, y_) in OUT.items(): tick("outcome", k_, "n", int(m_.sum()), "rate %.4f" % y_[m_].mean())

def crossfit(lab, seed=SEED):
    rs = np.random.default_rng(seed); half = rs.random(len(lab)) < 0.5; K = lab.max() + 1; res = {}
    for k_, (m_, y_) in OUT.items():
        score = np.full(len(lab), np.nan); tl = []
        for h in (True, False):
            tr = m_ & (half == h); te = m_ & (half != h)
            n_c = np.bincount(lab[tr], minlength=K); s_c = np.bincount(lab[tr], weights=y_[tr].astype(float), minlength=K)
            rate = np.where(n_c > 0, s_c / np.maximum(n_c, 1), y_[tr].mean()); score[te] = rate[lab[te]]
            best = int(np.argmax(np.where(n_c >= 200, rate, -1))); sel = te & (lab == best)
            tl.append(y_[sel].mean() / y_[te].mean() if sel.sum() > 0 and y_[te].mean() > 0 else np.nan)
        ok = m_ & ~np.isnan(score); res["auc_" + k_] = float(roc_auc_score(y_[ok], score[ok])); res["lift_" + k_] = float(np.nanmean(tl))
    return res
SIL = [np.random.default_rng(SEED + i).choice(len(A), 20000, replace=False) for i in range(3)]

rows = []
def family(name, XA_, XB_, ks):
    for k in ks:
        mA = KMeans(k, n_init=30, random_state=SEED).fit(XA_); lA = mA.labels_
        mB = KMeans(k, n_init=30, random_state=SEED).fit(XB_); lB = mB.labels_; lBA = mB.predict(XA_)
        rs = np.random.default_rng(SEED + k); hs = []
        for _ in range(2):
            perm = rs.permutation(len(XA_)); h1, h2 = perm[: len(perm) // 2], perm[len(perm) // 2:]
            m1 = KMeans(k, n_init=20, random_state=SEED).fit(XA_[h1]); m2 = KMeans(k, n_init=20, random_state=SEED + 1).fit(XA_[h2])
            hs.append(adjusted_rand_score(m1.predict(XA_), m2.predict(XA_)))
        p_ = np.bincount(lA) / len(lA)
        row = dict(method=name, k=k, half_ari=float(np.mean(hs)), temporal_ari=adjusted_rand_score(lA, lBA), inertia=float(mA.inertia_),
                   entropy=float(-(p_ * np.log(p_)).sum() / np.log(k)), min_share=float(p_.min()),
                   sil_common=float(np.mean([silhouette_score(XA[i], lA[i]) for i in SIL])), ch=float(calinski_harabasz_score(XA, lA)), db=float(davies_bouldin_score(XA, lA)))
        row.update(crossfit(lB)); rows.append(row)
        np.save(LAB / f"{name}_k{k}_A.npy", lA.astype(np.int16)); np.save(LAB / f"{name}_k{k}_B.npy", lB.astype(np.int16))
        pd.DataFrame(rows).to_csv(D / "s5_kselect.csv", index=False)
        tick(name, k, {a: round(b, 3) for a, b in row.items() if isinstance(b, float)})
family("M3", XA, XB, [6, 7, 8, 9, 10])
family("M2", RFMA, RFMB, [6, 7, 8, 9])
tick("done")
