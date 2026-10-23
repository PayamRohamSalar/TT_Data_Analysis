"""فاز ۲ - محک امکان‌سنجی فنی: زمان و حافظه‌ی روش‌های خوشه‌بندی روی کل مشتریان ۱۴۰۴ (بدون DB، بدون هدف تحلیلی).
ویژگی‌ها: ۹ ویژگی لگاریتمی/استاندارد از جدول مشتری×ماه سپرده؛ فقط برای سنجش مقیاس‌پذیری."""
from pathlib import Path
import time
import numpy as np, pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import MiniBatchKMeans, KMeans, Birch, AgglomerativeClustering, HDBSCAN
from sklearn.mixture import GaussianMixture
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

D = Path(__file__).resolve().parents[2] / "data" / "processed" / "phase2_clustering"
cm = pd.read_pickle(D / "customer_month_deposit.pkl")
d = cm[cm.ym // 100 == 1404].copy()
d["turn"] = ((d.crn + d.dbn) > 0).astype(np.int8)
g = d.groupby("customer_id")
X = pd.DataFrame({
    "bal": np.log1p(g.bal.mean()), "bal_end": np.log1p(g.bal.last()), "cr": np.log1p(g.cr.sum()), "db": np.log1p(g.db.sum()),
    "crn": np.log1p(g.crn.sum()), "dbn": np.log1p(g.dbn.sum()), "turn": g.turn.sum(), "acc": np.log1p(g.n_accounts.mean()),
    "cv": (g.bal.std() / g.bal.mean().replace(0, np.nan)).fillna(0).clip(0, 5)})
X = X.replace([np.inf, -np.inf], 0).fillna(0)
n = len(X); print("customers", n, "features", X.shape[1], flush=True)
Z = StandardScaler().fit_transform(X.values)
rng = np.random.default_rng(0)
log = []
def run(name, f):
    t = time.time()
    try:
        r = f(); s = f"{name}: {time.time()-t:.0f}s {r if r is not None else ''}"
    except Exception as e:
        s = f"{name}: FAILED {type(e).__name__} {str(e)[:120]} after {time.time()-t:.0f}s"
    print(s, flush=True); log.append(s)

t = time.time(); pca = PCA(6, random_state=0); P = pca.fit_transform(Z)
s0 = f"PCA 6 comps full: {time.time()-t:.0f}s var {pca.explained_variance_ratio_.sum():.3f}"; print(s0, flush=True); log.append(s0)
run("MiniBatchKMeans k=8 full", lambda: MiniBatchKMeans(8, random_state=0, n_init=3, batch_size=10000).fit(Z).inertia_)
run("KMeans k=8 full (n_init=3)", lambda: KMeans(8, random_state=0, n_init=3).fit(Z).inertia_)
run("GMM full-cov k=8 full (PCA6)", lambda: GaussianMixture(8, covariance_type="full", random_state=0, max_iter=60).fit(P).bic(P))
run("GMM diag k=8 full (Z)", lambda: GaussianMixture(8, covariance_type="diag", random_state=0, max_iter=60).fit(Z).bic(Z))
def birch():
    b = Birch(threshold=0.5, n_clusters=None).fit(P)
    return f"subclusters {len(b.subcluster_centers_)}"
run("BIRCH(PCA6) full", birch)
def ward_micro():
    mk = MiniBatchKMeans(1500, random_state=0, n_init=1, batch_size=20000).fit(Z)
    ag = AgglomerativeClustering(8, linkage="ward").fit(mk.cluster_centers_)
    return f"micro 1500 -> ward k=8 ok"
run("Ward on 1500 micro-clusters (full data)", ward_micro)
run("Ward exact on 20k sample", lambda: AgglomerativeClustering(8, linkage="ward").fit(Z[rng.choice(n, 20000, replace=False)]).n_clusters_)
for m in (50000, 100000, 200000):
    idx = rng.choice(n, m, replace=False)
    run(f"HDBSCAN PCA6 n={m}", lambda: (lambda h: f"clusters {h.labels_.max()+1} noise {(h.labels_==-1).mean():.2f}")(HDBSCAN(min_cluster_size=200, n_jobs=-1).fit(P[idx])))
idx = rng.choice(n, 50000, replace=False)
lab = MiniBatchKMeans(8, random_state=0, n_init=3).fit_predict(Z)
run("silhouette on 50k sample (evaluation)", lambda: round(silhouette_score(Z[idx], lab[idx]), 3))
(D / "feasibility_benchmark.txt").write_text("\n".join(log), encoding="utf-8")
