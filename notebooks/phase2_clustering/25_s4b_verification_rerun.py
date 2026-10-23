"""فاز ۲ - S4b: اصلاح S4 پس از داوری مستقل (بدون DB).
(۱) بازبرازش خانواده‌ی K-Means (M2، M3، M3n، M8) با n_init بالا و بازمحاسبه‌ی پایداری نیم‌نمونه و زمانی؛
(۲) اعتبار بیرونی با ROC AUC و lift با برازش متقاطع (نرخ خوشه از نیمه‌ی دیگر) برای همه‌ی روش‌ها؛
(۳) silhouette در فضای آموزش خود روش برای M2 و M8؛ (۴) توزیع وام‌داران با سپرده‌ی صوری در خوشه‌های M3.
خروجی: s4b_kmeans_family.csv، s4b_external_auc.csv، s4b_own_space_silhouette.csv، s4b_token_borrowers.csv، s4_labels/*_n30.npy"""
import sys, time
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, roc_auc_score, silhouette_score
from tt_bank.phase2_clustering.prep import Prep, raw_transform

D = Path(__file__).resolve().parents[2] / "data" / "processed" / "phase2_clustering"; LAB = D / "s4_labels"
t0 = time.time()
def tick(*a): print(f"[{time.time()-t0:6.0f}s]", *a, flush=True)
SEED = 20261021

F = pd.read_pickle(D / "features_customer_year.pkl"); M = F[F.category == "model"]
prep = Prep.from_json(D / "prep_spec.json")
A = M[M.y == 1404].reset_index(drop=True); B = M[M.y == 1403].reset_index(drop=True)
XA, XB = prep.transform(A), prep.transform(B)
prep_nb = Prep().fit(M[M.y == 1404], block_weights=False, panel=M)
XA_nb, XB_nb = prep_nb.transform(A), prep_nb.transform(B)
rfm = pd.read_pickle(D / "rfm_scores.pkl")
def rf(df): return df[["customer_id", "y"]].merge(rfm[["customer_id", "y", "R", "F", "M", "L"]], on=["customer_id", "y"], how="left")
RA, RB = rf(A), rf(B)
RFMA = np.column_stack([RA.R, RA.F, RA.M, RA.L, A.has_loan_dec.to_numpy()]).astype("float32")
RFMB = np.column_stack([RB.R, RB.F, RB.M, RB.L, B.has_loan_dec.to_numpy()]).astype("float32")
Mal = prep._align(M); Rw = raw_transform(Mal)
Tcols = pd.DataFrame({"customer_id": M.customer_id.to_numpy(), "y": M.y.to_numpy(), "bal": Rw.bal_mean_log.to_numpy(), "turn": Rw.turn_share.to_numpy(),
                      "loan": Rw.has_loan.to_numpy(), "loanlog": Rw.loan_log.to_numpy()})
def traj(df, t):
    X_ = np.zeros((len(df), 17), dtype="float32"); npres = np.zeros(len(df))
    for i, y in enumerate(range(t - 3, t + 1)):
        r = Tcols[Tcols.y == y].set_index("customer_id").reindex(df.customer_id.to_numpy())
        for c, name in enumerate(["bal", "turn", "loan", "loanlog"]): X_[:, i * 4 + c] = r[name].fillna(0).to_numpy()
        npres += r.bal.notna().to_numpy()
    X_[:, -1] = npres; return X_
TA, TB = traj(A, 1404), traj(B, 1403); mu, sd = TA.mean(0), TA.std(0) + 1e-6; TA, TB = (TA - mu) / sd, (TB - mu) / sd

# پیامدها (همان تعریف S4)
N = F[F.y == 1404].set_index("customer_id"); nxt = N.reindex(B.customer_id.to_numpy())
present = B.customer_id.isin(N.index).to_numpy()
bal_now, bal_next = B.bal_dec.fillna(0).to_numpy(), nxt.bal_dec.fillna(0).to_numpy()
OUT = {"loan_uptake": (B.has_loan_dec.to_numpy() == 0, (nxt.has_loan_dec.fillna(0).to_numpy() == 1) & present),
       "balance_halved": (bal_now > 0, (~present) | (bal_next < 0.5 * bal_now)),
       "dormant_next": (np.ones(len(B), bool), (~present) | (nxt.category.fillna("").to_numpy() == "idle_token") | (nxt.turn_share.fillna(0).to_numpy() < 0.25)),
       "npl_entry": ((B.has_loan_dec.to_numpy() == 1) & (B.npl_share.to_numpy() == 0), present & (nxt.npl_share.fillna(0).to_numpy() > 0))}
tick("data ready")

def crossfit(lab, seed=SEED):
    """AUC و lift بالاترین خوشه با برازش متقاطع: نرخ هر خوشه از نیمه‌ی دیگر برآورد می‌شود."""
    rs = np.random.default_rng(seed); half = rs.random(len(lab)) < 0.5
    lab = np.where(lab < 0, lab.max() + 1, lab); K = lab.max() + 1; res = {}
    for k_, (m_, y_) in OUT.items():
        score = np.full(len(lab), np.nan); top_lift = []
        for h in (True, False):
            tr = m_ & (half == h); te = m_ & (half != h)
            n_c = np.bincount(lab[tr], minlength=K); s_c = np.bincount(lab[tr], weights=y_[tr].astype(float), minlength=K)
            rate = np.where(n_c > 0, s_c / np.maximum(n_c, 1), y_[tr].mean())
            score[te] = rate[lab[te]]
            best = int(np.argmax(np.where(n_c >= 200, rate, -1)))
            sel = te & (lab == best)
            top_lift.append(y_[sel].mean() / y_[te].mean() if sel.sum() > 0 and y_[te].mean() > 0 else np.nan)
        ok = m_ & ~np.isnan(score)
        res["auc_" + k_] = float(roc_auc_score(y_[ok], score[ok])); res["lift_" + k_] = float(np.nanmean(top_lift))
    return res

def own_sil(X, lab, n=20000, reps=3):
    rs = np.random.default_rng(SEED); out = []
    for _ in range(reps):
        i = rs.choice(len(X), n, replace=False); out.append(silhouette_score(X[i], lab[i]))
    return float(np.mean(out))

rows = []
def run_family(name, XA_, XB_, ks):
    for k in ks:
        mA = KMeans(k, n_init=30, random_state=SEED).fit(XA_); lA = mA.labels_
        mB = KMeans(k, n_init=30, random_state=SEED).fit(XB_); lB = mB.labels_; lBA = mB.predict(XA_)
        rs = np.random.default_rng(SEED + k); hs = []
        for _ in range(2):
            perm = rs.permutation(len(XA_)); h1, h2 = perm[: len(perm) // 2], perm[len(perm) // 2:]
            m1 = KMeans(k, n_init=20, random_state=SEED).fit(XA_[h1]); m2 = KMeans(k, n_init=20, random_state=SEED + 1).fit(XA_[h2])
            hs.append(adjusted_rand_score(m1.predict(XA_), m2.predict(XA_)))
        np.save(LAB / f"{name}_k{k}_A_n30.npy", lA.astype(np.int16)); np.save(LAB / f"{name}_k{k}_B_n30.npy", lB.astype(np.int16))
        row = dict(method=name, k=k, half_ari_n30=float(np.mean(hs)), temporal_ari_n30=adjusted_rand_score(lA, lBA), inertia=float(mA.inertia_))
        row.update(crossfit(lB)); rows.append(row)
        pd.DataFrame(rows).to_csv(D / "s4b_kmeans_family.csv", index=False)
        tick(name, k, {a: round(b, 3) for a, b in row.items() if isinstance(b, float)})

for name, XA_, XB_, ks in [("M3", XA, XB, [4, 5, 6, 7, 8, 9, 10]), ("M3n", XA_nb, XB_nb, [5, 6, 7, 8, 9]), ("M2", RFMA, RFMB, [5, 6, 7, 8, 9]), ("M8", TA, TB, [5, 6, 7, 8, 9])]:
    run_family(name, XA_, XB_, ks)

# AUC متقاطع برای بقیه‌ی روش‌ها (برچسب‌های S4 اصلی)
raw = pd.read_csv(D / "s4_scorecard_raw.csv")
others = []
for r in raw.itertuples():
    if r.method in ("M3", "M3n", "M2", "M8"): continue
    f = LAB / f"{r.method}_k{int(r.k)}_B.npy"
    if not f.exists(): f = LAB / f"{r.method}_kNA_B.npy"
    if not f.exists(): continue
    row = dict(method=r.method, k=int(r.k)); row.update(crossfit(np.load(f).astype(int))); others.append(row)
    tick("crossfit", r.method, r.k)
fam = pd.DataFrame(rows)
allx = pd.concat([fam[["method", "k"] + [c for c in fam.columns if c.startswith(("auc_", "lift_"))]], pd.DataFrame(others)], ignore_index=True)
allx.to_csv(D / "s4b_external_auc.csv", index=False)

# silhouette در فضای آموزش خود روش
sil = []
for name, X_, k in [("M2", RFMA, 7), ("M2", RFMA, 5), ("M2", RFMA, 9), ("M8", TA, 7), ("M8", TA, 5), ("M8", TA, 9), ("M3", XA, 8), ("M3", XA, 7)]:
    lab = np.load(LAB / f"{name}_k{k}_A_n30.npy").astype(int); sil.append(dict(method=name, k=k, silhouette_own_space=own_sil(X_, lab), silhouette_common_space=own_sil(XA, lab)))
pd.DataFrame(sil).to_csv(D / "s4b_own_space_silhouette.csv", index=False); tick("own-space silhouette done")

# وام‌داران با سپرده‌ی صوری در خوشه‌های M3 (k=8)
pan = pd.read_pickle(D / "panel_customer_year.pkl"); pa = pan[pan.y == 1404].set_index("customer_id").reindex(A.customer_id.to_numpy())
token = (A.has_primary_loan.to_numpy()) & ((pa.turn_months.to_numpy() < 3) | (pa.bal_max.to_numpy() < 5e6))
lab8 = np.load(LAB / "M3_k8_A_n30.npy").astype(int)
ct = pd.crosstab(lab8, token, margins=True); ct.columns = ["not_token", "token", "all"]; ct["token_share_of_cluster"] = ct.token / ct["all"]; ct["cluster_share_of_token"] = ct.token / ct.token.iloc[-1]
ct.to_csv(D / "s4b_token_borrowers.csv"); print(ct.round(3).to_string()); tick("done")
