"""فاز ۲ - S3: آزمون نمایش اندازه: ریال ثابت (تعدیل CPI) در برابر هم‌ترازی چندکی درون سال.
معیار: همخوانی خوشه‌های مرکز-ثابت (آموزش 1404) با خوشه‌بندی مستقل همان سال (ARI) نسبت به سقف دو بذر؛ و رانش سهم خوشه‌ها."""
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
from tt_bank.phase2_clustering.prep import Prep, NAMES

D = Path(__file__).resolve().parents[2] / "data" / "processed" / "phase2_clustering"
F = pd.read_pickle(D / "features_customer_year.pkl")
M = F[F.category == "model"]
ref = M[M.y == 1404]
K = 8
out = []
def km(X, seed): return KMeans(K, n_init=5, random_state=seed).fit(X)
for name, aligned in (("real_cpi", False), ("quantile_aligned", True)):
    prep = Prep().fit(ref, panel=M if aligned else None)
    if aligned: prep.to_json(D / "prep_spec.json")
    m_ref = km(prep.transform(ref, aligned=aligned), 0)
    for y in (1403, 1402, 1401, 1400):
        d = M[M.y == y]; X = prep.transform(d, aligned=aligned)
        fixed = m_ref.predict(X)
        own0, own1 = km(X, 0), km(X, 1)
        ceiling = adjusted_rand_score(own0.labels_, own1.labels_)
        ari = adjusted_rand_score(fixed, own0.labels_)
        sizes = np.bincount(fixed, minlength=K) / len(fixed)
        # سهم خوشه‌ی کم‌اندازه‌ترین مرکز (کمترین bal_mean_log) در این سال
        low = int(np.argmin(m_ref.cluster_centers_[:, NAMES.index("bal_mean_log")]))
        out.append(dict(rep=name, year=y, n=len(d), ari_fixed_vs_own=ari, ari_seed_ceiling=ceiling, ratio=ari / ceiling,
                        share_lowest_size_cluster=sizes[low], max_share=sizes.max(), min_share=sizes.min()))
        print(out[-1], flush=True)
    d = ref; sizes = np.bincount(m_ref.labels_, minlength=K) / len(ref)
    out.append(dict(rep=name, year=1404, n=len(ref), ari_fixed_vs_own=1.0, ari_seed_ceiling=np.nan, ratio=np.nan,
                    share_lowest_size_cluster=sizes[int(np.argmin(m_ref.cluster_centers_[:, NAMES.index("bal_mean_log")]))], max_share=sizes.max(), min_share=sizes.min()))
pd.DataFrame(out).to_csv(D / "s3_temporal_alignment_test.csv", index=False)
