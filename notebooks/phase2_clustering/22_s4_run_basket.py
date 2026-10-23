"""فاز ۲ - S4: اجرای سبد روش‌های خوشه‌بندی روی کل گروه مدل و محاسبه‌ی معیارهای کارت امتیاز (بدون DB).
سال A = 1404 (داخلی، پایداری، پروفایل)؛ سال B = 1403 (اعتبار بیرونی روی پیامدهای 1404، پایداری زمانی).
استفاده: python -u 22_s4_run_basket.py [methods...]   مثال: M3 M3n M2 M4 M5 M6 M8 M7 M9 M1
خروجی‌ها: s4_scorecard_raw.csv (افزایشی)، s4_labels/*.npy"""
import sys, time, json
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.cluster import KMeans, MiniBatchKMeans, AgglomerativeClustering, HDBSCAN
from sklearn.decomposition import PCA
from sklearn.mixture import GaussianMixture
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import adjusted_rand_score, silhouette_score, calinski_harabasz_score, davies_bouldin_score
from tt_bank.phase2_clustering.prep import Prep, NAMES, raw_transform

D = Path(__file__).resolve().parents[2] / "data" / "processed" / "phase2_clustering"
LAB = D / "s4_labels"; LAB.mkdir(exist_ok=True)
OUTCSV = D / "s4_scorecard_raw.csv"
KS = [5, 6, 7, 8, 9]
KS_EXTRA = {"M3": [4, 10]}
rng = np.random.default_rng(42)
t0 = time.time()
def tick(*a): print(f"[{time.time()-t0:6.0f}s]", *a, flush=True)

# ------------------------------------------------------------------ داده
F = pd.read_pickle(D / "features_customer_year.pkl")
M = F[F.category == "model"]
prep = Prep.from_json(D / "prep_spec.json")
A = M[M.y == 1404].reset_index(drop=True); B = M[M.y == 1403].reset_index(drop=True)
XA, XB = prep.transform(A), prep.transform(B)
prep_nb = Prep().fit(M[M.y == 1404], block_weights=False, panel=M)
XA_nb, XB_nb = prep_nb.transform(A), prep_nb.transform(B)
rfm = pd.read_pickle(D / "rfm_scores.pkl")
def rf(df):
    return df[["customer_id", "y"]].merge(rfm[["customer_id", "y", "R", "F", "M", "L", "R_q", "F_q", "M_q", "L_q"]], on=["customer_id", "y"], how="left")
RA, RB = rf(A), rf(B)
tick("data", XA.shape, XB.shape)

# پیامدهای 1404 برای مشتریان B (1403)
N = F[F.y == 1404].set_index("customer_id")
j = B.customer_id.map(lambda c: c in N.index).to_numpy()
nxt = N.reindex(B.customer_id.to_numpy())
present = j
bal_now, bal_next = B.bal_dec.fillna(0).to_numpy(), nxt.bal_dec.fillna(0).to_numpy()
OUT = {}
m0 = (B.has_loan_dec.to_numpy() == 0)
OUT["loan_uptake"] = (m0, (nxt.has_loan_dec.fillna(0).to_numpy() == 1) & present)
m1 = bal_now > 0
OUT["balance_halved"] = (m1, (~present) | (bal_next < 0.5 * bal_now))
OUT["dormant_next"] = (np.ones(len(B), bool), (~present) | (nxt.category.fillna("").to_numpy() == "idle_token") | (nxt.turn_share.fillna(0).to_numpy() < 0.25))
m3 = (B.has_loan_dec.to_numpy() == 1) & (B.npl_share.to_numpy() == 0)
OUT["npl_entry"] = (m3, present & (nxt.npl_share.fillna(0).to_numpy() > 0))
for k_, (m_, y_) in OUT.items():
    tick("outcome", k_, "n", int(m_.sum()), "rate %.4f" % y_[m_].mean())

# مسیر (M8): سال‌های t-3..t، ویژگی‌های هم‌ترازشده
Mal = prep._align(M)
Rw = raw_transform(Mal)
Tcols = pd.DataFrame({"customer_id": M.customer_id.to_numpy(), "y": M.y.to_numpy(), "bal": Rw.bal_mean_log.to_numpy(), "turn": Rw.turn_share.to_numpy(),
                      "loan": Rw.has_loan.to_numpy(), "loanlog": Rw.loan_log.to_numpy()})
def traj(df, t):
    X_ = np.zeros((len(df), 4 * 4 + 1), dtype="float32"); npres = np.zeros(len(df))
    for i, y in enumerate(range(t - 3, t + 1)):
        s = Tcols[Tcols.y == y].set_index("customer_id")
        r = s.reindex(df.customer_id.to_numpy())
        ok = r.bal.notna().to_numpy()
        for c, name in enumerate(["bal", "turn", "loan", "loanlog"]):
            X_[:, i * 4 + c] = r[name].fillna(0).to_numpy()
        npres += ok
    X_[:, -1] = npres
    return X_
TA, TB = traj(A, 1404), traj(B, 1403)
mu, sd = TA.mean(0), TA.std(0) + 1e-6
TA, TB = (TA - mu) / sd, (TB - mu) / sd
tick("trajectory", TA.shape)

# ارزش RFM برای M4
def tier(Rdf, ref_q=None):
    V = 0.6 * Rdf.M.to_numpy() + 0.4 * Rdf.L.to_numpy()
    q = ref_q if ref_q is not None else np.quantile(V, [0.5, 0.9, 0.99])
    return np.digitize(V, q), q

# ------------------------------------------------------------------ سنجه‌ها
def entropy(lab):
    p_ = np.bincount(lab[lab >= 0]) / (lab >= 0).sum(); p_ = p_[p_ > 0]
    return float(-(p_ * np.log(p_)).sum() / np.log(len(p_))) if len(p_) > 1 else 0.0
SIL_IDX = [rng.choice(len(XA), 20000, replace=False) for _ in range(3)]
def internal(lab):
    ok = lab >= 0
    if len(np.unique(lab[ok])) < 2: return dict(sil=np.nan, ch=np.nan, db=np.nan)
    s = np.mean([silhouette_score(XA[i][ok[i]], lab[i][ok[i]]) for i in SIL_IDX]) if ok.mean() > 0.5 else np.nan
    return dict(sil=float(s), ch=float(calinski_harabasz_score(XA[ok], lab[ok])), db=float(davies_bouldin_score(XA[ok], lab[ok])))
def adjr2(y, lab, mask):
    y = y[mask].astype(float); l = lab[mask]
    if len(np.unique(l)) < 2: return np.nan
    g = pd.Series(y).groupby(l).agg(["mean", "count"])
    sst = ((y - y.mean()) ** 2).sum()
    ssb = (g["count"] * (g["mean"] - y.mean()) ** 2).sum()
    r2 = ssb / sst if sst > 0 else 0
    n_, k_ = len(y), len(g)
    return float(1 - (1 - r2) * (n_ - 1) / (n_ - k_))
def lift(y, lab, mask):
    y = y[mask].astype(float); l = lab[mask]
    g = pd.Series(y).groupby(l).mean()
    return float(g.max() / y.mean()) if y.mean() > 0 else np.nan
def external(labB):
    d = {}
    for k_, (m_, y_) in OUT.items():
        d["adjr2_" + k_] = adjr2(y_, labB, m_); d["lift_" + k_] = lift(y_, labB, m_)
    return d

# ------------------------------------------------------------------ یادگیرنده‌ها
class KM:
    def __init__(self, k, n_init=10): self.m = KMeans(k, n_init=n_init, random_state=0)
    def fit(self, X): self.m.fit(X); return self
    def predict(self, X): return self.m.predict(X)
class GM:
    def __init__(self, k): self.k = k
    def fit(self, X):
        self.p = PCA(12, random_state=0).fit(X); Z = self.p.transform(X)
        self.m = GaussianMixture(self.k, covariance_type="full", n_init=1, random_state=0, max_iter=80, reg_covar=1e-4).fit(Z)
        self.bic = float(self.m.bic(Z)); return self
    def predict(self, X): return self.m.predict(self.p.transform(X))
class WD:
    def __init__(self, k): self.k = k
    def fit(self, X):
        self.mb = MiniBatchKMeans(1500, random_state=0, n_init=1, batch_size=20000).fit(X)
        ag = AgglomerativeClustering(self.k, linkage="ward").fit(self.mb.cluster_centers_)
        self.map = ag.labels_; return self
    def predict(self, X): return self.map[self.mb.predict(X)]
class HD:
    """HDBSCAN روی زیرنمونه‌ی 100 هزارتایی (برازش روی کل 636 هزار مشتری بیش از 45 دقیقه برای یک برازش طول کشید) و تعمیم با k نزدیک‌ترین همسایه."""
    def __init__(self, frac, sub=100000): self.frac, self.sub = frac, sub
    def fit(self, X):
        self.p = PCA(6, random_state=0).fit(X); Z = self.p.transform(X)
        idx = rng.choice(len(Z), min(self.sub, len(Z)), replace=False)
        h = HDBSCAN(min_cluster_size=int(self.frac * len(idx)), min_samples=50, n_jobs=-1).fit(Z[idx])
        ok = h.labels_ >= 0
        self.knn = KNeighborsClassifier(15, n_jobs=-1).fit(Z[idx][ok], h.labels_[ok]) if ok.any() else None
        self.noise_sub = float((~ok).mean())
        # برچسب همه‌ی مشتریان: نزدیک‌ترین هسته؛ نویز زیرنمونه با فاصله‌ی دور نویز می‌ماند
        self.lab = self.predict(X, Z=Z)
        return self
    def predict(self, X, Z=None):
        if self.knn is None: return -np.ones(len(X), int)
        Z = self.p.transform(X) if Z is None else Z
        lab = self.knn.predict(Z)
        d, _ = self.knn.kneighbors(Z, n_neighbors=1)
        thr = getattr(self, "thr", None)
        if thr is None:
            self.thr = float(np.quantile(d[:, 0], 0.97)); thr = self.thr
        lab[d[:, 0] > thr] = -1
        return lab

class TwoStage:
    """M4: رده‌ی ارزشی RFM-L (4 رده) و سپس K-Means درون هر رده."""
    def __init__(self, k, Rdf): self.k, self.Rdf = k, Rdf
    def fit(self, X, Rdf=None):
        Rdf = self.Rdf if Rdf is None else Rdf
        t, self.q = tier(Rdf)
        n = np.bincount(t, minlength=4).astype(float); w = np.sqrt(n); kk = np.maximum(1, np.floor(self.k * w / w.sum()).astype(int))
        while kk.sum() < self.k: kk[np.argmax(w / kk)] += 1
        while kk.sum() > self.k: kk[np.argmax(kk)] -= 1
        self.kk = kk; self.ms = []; off = 0; self.off = []
        for g in range(4):
            idx = t == g
            m = KMeans(int(kk[g]), n_init=5, random_state=0).fit(X[idx]) if kk[g] > 1 else None
            self.ms.append(m); self.off.append(off); off += int(kk[g])
        return self
    def predict(self, X, Rdf):
        t, _ = tier(Rdf, self.q); lab = np.zeros(len(X), int)
        for g in range(4):
            idx = t == g
            if not idx.any(): continue
            lab[idx] = self.off[g] + (self.ms[g].predict(X[idx]) if self.ms[g] is not None else 0)
        return lab

def rule_m1(Rdf):
    Mq, Fq, L = Rdf.M_q.to_numpy(), Rdf.F_q.to_numpy(), Rdf.L.to_numpy()
    lab = np.full(len(Rdf), 6)
    conds = [(Mq == 5) & (Fq >= 4), (Mq >= 4) & (Fq >= 3), (L > 0) & (Fq >= 3), (L > 0) & (Fq < 3), (Mq >= 3) & (Fq < 3), (Mq <= 2) & (Fq >= 3)]
    done = np.zeros(len(Rdf), bool)
    for i, c in enumerate(conds):
        m = c & ~done; lab[m] = i; done |= m
    return lab

# ------------------------------------------------------------------ اجرا
def halves(make, X, nrep=2):
    """پایداری نیم‌نمونه: دو مدل روی دو نیمه‌ی تصادفی، ARI پیش‌بینی روی کل داده."""
    out = []
    for r in range(nrep):
        perm = rng.permutation(len(X)); h1, h2 = perm[: len(X) // 2], perm[len(X) // 2:]
        m1, m2 = make().fit(X[h1]), make().fit(X[h2])
        out.append(adjusted_rand_score(m1.predict(X), m2.predict(X)))
    return float(np.mean(out))
def append(rows):
    df = pd.DataFrame(rows)
    if OUTCSV.exists():
        old = pd.read_csv(OUTCSV); df = pd.concat([old[~old.set_index(["method", "k"]).index.isin(df.set_index(["method", "k"]).index)], df], ignore_index=True)
    df.to_csv(OUTCSV, index=False)

def run_generic(name, ks, make, XA_, XB_, with_halves=True, rdf=False):
    for k in ks:
        row = dict(method=name, k=k)
        mA = make(k, "A"); mA.fit(XA_) if not rdf else mA.fit(XA_, RA)
        lA = mA.predict(XA_) if not rdf else mA.predict(XA_, RA)
        mB = make(k, "B"); mB.fit(XB_) if not rdf else mB.fit(XB_, RB)
        lB = mB.predict(XB_) if not rdf else mB.predict(XB_, RB)
        lBA = mB.predict(XA_) if not rdf else mB.predict(XA_, RA)
        np.save(LAB / f"{name}_k{k}_A.npy", lA.astype(np.int16)); np.save(LAB / f"{name}_k{k}_B.npy", lB.astype(np.int16))
        row.update(n_clusters=len(np.unique(lA[lA >= 0])), noise_share=float((lA < 0).mean()), min_share=float(np.bincount(lA[lA >= 0]).min() / len(lA)),
                   entropy=entropy(lA), temporal_ari=adjusted_rand_score(lA, lBA))
        row.update(internal(lA)); row.update(external(lB))
        if hasattr(mA, "bic"): row["bic"] = mA.bic
        if with_halves and not rdf:
            row["half_ari"] = halves(lambda: make(k, "H"), XA_)
        append([row]); tick(name, "k", k, {kk: round(v, 3) for kk, v in row.items() if isinstance(v, float)})

methods = sys.argv[1:] or ["M3", "M3n", "M2", "M4", "M5", "M6", "M8", "M7", "M1", "M9"]
RFMA = np.column_stack([RA.R, RA.F, RA.M, RA.L, (A.has_loan_dec.to_numpy())]).astype("float32")
RFMB = np.column_stack([RB.R, RB.F, RB.M, RB.L, (B.has_loan_dec.to_numpy())]).astype("float32")
for m in methods:
    tick("method", m)
    if m == "M3":
        for k in sorted(set(KS + KS_EXTRA.get("M3", []))): run_generic("M3", [k], lambda k_, s: KM(k_, 3 if s == "H" else 10), XA, XB)
    elif m == "M3n": run_generic("M3n", KS, lambda k_, s: KM(k_, 3 if s == "H" else 10), XA_nb, XB_nb)
    elif m == "M2": run_generic("M2", KS, lambda k_, s: KM(k_, 3 if s == "H" else 10), RFMA, RFMB)
    elif m == "M5": run_generic("M5", KS, lambda k_, s: GM(k_), XA, XB)
    elif m == "M6": run_generic("M6", KS, lambda k_, s: WD(k_), XA, XB)
    elif m == "M8": run_generic("M8", KS, lambda k_, s: KM(k_, 3 if s == "H" else 10), TA, TB)
    elif m == "M4": run_generic("M4", KS, lambda k_, s: TwoStage(k_, RA if s != "B" else RB), XA, XB, with_halves=False, rdf=True)
    elif m == "M1":
        lA, lB = rule_m1(RA), rule_m1(RB)
        row = dict(method="M1", k=7, n_clusters=len(np.unique(lA)), noise_share=0.0, min_share=float(np.bincount(lA).min() / len(lA)), entropy=entropy(lA),
                   temporal_ari=adjusted_rand_score(lA, rule_m1(RA)), half_ari=np.nan)
        row.update(internal(lA)); row.update(external(lB)); np.save(LAB / "M1_k7_A.npy", lA.astype(np.int16)); np.save(LAB / "M1_k7_B.npy", lB.astype(np.int16))
        append([row]); tick("M1", {kk: round(v, 3) for kk, v in row.items() if isinstance(v, float)})
    elif m == "M7":
        for mcs in (3000,):
            fr = mcs / 636016
            name = f"M7_{mcs}"; mA = HD(fr).fit(XA); lA = mA.lab.copy(); mB = HD(fr).fit(XB); lB = mB.lab.copy(); lBA = mB.predict(XA)
            np.save(LAB / f"{name}_kNA_A.npy", lA.astype(np.int16)); np.save(LAB / f"{name}_kNA_B.npy", lB.astype(np.int16))
            ok = lA >= 0
            row = dict(method=name, k=int(lA.max() + 1), n_clusters=int(lA.max() + 1), noise_share=float((~ok).mean()), min_share=float(np.bincount(lA[ok]).min() / len(lA)) if ok.any() else np.nan,
                       entropy=entropy(lA), temporal_ari=adjusted_rand_score(lA, lBA), half_ari=np.nan)
            row.update(internal(lA)); row.update(external(np.where(lB < 0, lB.max() + 1, lB)))
            append([row]); tick(name, {kk: round(v, 3) for kk, v in row.items() if isinstance(v, float)})
    elif m == "M9":
        mem = ["M2", "M3", "M4", "M5", "M6", "M8"]
        for k in KS:
            try:
                LA = np.column_stack([np.load(LAB / f"{x}_k{k}_A.npy") for x in mem]); LB = np.column_stack([np.load(LAB / f"{x}_k{k}_B.npy") for x in mem])
            except FileNotFoundError as e:
                tick("M9 skip", k, e); continue
            def onehot(L_, k=k): return np.hstack([np.eye(k, dtype="float32")[L_[:, i]] for i in range(L_.shape[1])])
            OA, OB = onehot(LA), onehot(LB)
            mA = KMeans(k, n_init=10, random_state=0).fit(OA); lA = mA.labels_; mB = KMeans(k, n_init=10, random_state=0).fit(OB); lB = mB.labels_
            # پایداری زمانی: پیش‌بینی اعضای B روی A سپس نزدیک‌ترین مرکز B
            lBA = None
            row = dict(method="M9", k=k, n_clusters=k, noise_share=0.0, min_share=float(np.bincount(lA).min() / len(lA)), entropy=entropy(lA), temporal_ari=np.nan, half_ari=np.nan)
            row.update(internal(lA)); row.update(external(lB))
            np.save(LAB / f"M9_k{k}_A.npy", lA.astype(np.int16)); np.save(LAB / f"M9_k{k}_B.npy", lB.astype(np.int16))
            append([row]); tick("M9", k, {kk: round(v, 3) for kk, v in row.items() if isinstance(v, float)})
tick("done")
