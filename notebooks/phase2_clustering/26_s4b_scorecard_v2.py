"""فاز ۲ - S4b: کارت امتیاز نسخه‌ی 2 پس از داوری: اعتبار بیرونی با AUC و lift (برازش متقاطع)، پایداری با n_init بالا،
حذف وفاداری درخت از رتبه‌دهی، معیار داخلی در فضای مشترک (و حالت بدون معیار داخلی). بدون DB."""
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score
from tt_bank.phase2_clustering.prep import Prep

D = Path(__file__).resolve().parents[2] / "data" / "processed" / "phase2_clustering"; LAB = D / "s4_labels"
OUTS = ["loan_uptake", "balance_halved", "dormant_next", "npl_entry"]
old = pd.read_csv(D / "s4_scorecard_full.csv")
fam = pd.read_csv(D / "s4b_kmeans_family.csv"); ext = pd.read_csv(D / "s4b_external_auc.csv")
F = pd.read_pickle(D / "features_customer_year.pkl"); A = F[(F.category == "model") & (F.y == 1404)].reset_index(drop=True)
prep = Prep.from_json(D / "prep_spec.json"); XA = prep.transform(A)
rs = np.random.default_rng(20261021); IDX = [rs.choice(len(XA), 20000, replace=False) for _ in range(3)]

def internal(lab):
    ok = lab >= 0
    if len(np.unique(lab[ok])) < 2: return dict(sil=np.nan, ch=np.nan, db=np.nan)
    return dict(sil=float(np.mean([silhouette_score(XA[i][ok[i]], lab[i][ok[i]]) for i in IDX])),
                ch=float(calinski_harabasz_score(XA[ok], lab[ok])), db=float(davies_bouldin_score(XA[ok], lab[ok])))

rows = []
for r in old.itertuples():
    base = dict(method=r.method, k=int(r.k), entropy=r.entropy, min_share=r.min_share, half_ari=r.half_ari, temporal_ari=r.temporal_ari, sil=r.sil, ch=r.ch, db=r.db)
    f = fam[(fam.method == r.method) & (fam.k == r.k)]
    if len(f):
        f = f.iloc[0]; lab = np.load(LAB / f"{r.method}_k{int(r.k)}_A_n30.npy").astype(int)
        p_ = np.bincount(lab) / len(lab)
        base.update(half_ari=f.half_ari_n30, temporal_ari=f.temporal_ari_n30, entropy=float(-(p_ * np.log(p_)).sum() / np.log(len(p_))), min_share=float(p_.min()), **internal(lab))
    e = ext[(ext.method == r.method) & (ext.k == r.k)]
    if len(e):
        e = e.iloc[0]
        for o in OUTS: base["auc_" + o] = e["auc_" + o]; base["lift_" + o] = e["lift_" + o]
    rows.append(base)
R = pd.DataFrame(rows)
R["auc_mean"] = R[[f"auc_{o}" for o in OUTS]].mean(axis=1); R["lift_mean"] = R[[f"lift_{o}" for o in OUTS]].mean(axis=1)
R = R[R.method != "M7_3000"]
R.to_csv(D / "s4b_scorecard_v2_full.csv", index=False, encoding="utf-8-sig")

def score_frame(R_, w):
    rows = []
    for k, g in R_.groupby("k"):
        if len(g) < 2: continue
        def rk(col, high=True):
            r = g[col].rank(ascending=not high, method="average", na_option="keep")
            return 1 - (r - 1) / (r.max() - 1) if r.max() > 1 else r * 0 + 0.5
        internal_ = pd.concat([rk("sil"), rk("ch"), rk("db", high=False)], axis=1).mean(axis=1)
        stability = pd.concat([rk("half_ari"), rk("temporal_ari")], axis=1).mean(axis=1)
        external = pd.concat([rk("auc_mean"), rk("lift_mean")], axis=1).mean(axis=1)
        usability = pd.concat([rk("entropy"), rk("min_share")], axis=1).mean(axis=1)
        for idx in g.index:
            parts = dict(internal=internal_[idx], stability=stability[idx], external=external[idx], usability=usability[idx])
            num = sum(w[p] * (0 if pd.isna(v) else v) for p, v in parts.items() if w[p] > 0 and not pd.isna(v))
            den = sum(w[p] for p, v in parts.items() if w[p] > 0 and not pd.isna(v))
            rows.append(dict(method=g.loc[idx, "method"], k=k, **parts, composite=num / den if den else np.nan))
    return pd.DataFrame(rows)

W = {"base": dict(internal=.25, stability=.30, external=.30, usability=.15),
     "equal": dict(internal=.25, stability=.25, external=.25, usability=.25),
     "external_heavy": dict(internal=.15, stability=.25, external=.45, usability=.15),
     "no_internal": dict(internal=0, stability=.35, external=.45, usability=.20)}
S = {n: score_frame(R, w) for n, w in W.items()}
S["base"].to_csv(D / "s4b_scores_by_k.csv", index=False)
rank = pd.DataFrame({n: s.groupby("method").composite.mean() for n, s in S.items()})
for n in W: rank["rank_" + n] = rank[n].rank(ascending=False)
rank["borda"] = rank[[f"rank_{n}" for n in W]].mean(axis=1); rank = rank.sort_values("borda")
rank.to_csv(D / "s4b_method_ranking_v2.csv", encoding="utf-8-sig"); print(rank.round(3).to_string())
best = S["base"].sort_values("composite", ascending=False).groupby("method").head(1).sort_values("composite", ascending=False)
best.to_csv(D / "s4b_best_k_by_method_v2.csv", index=False); print(best.round(3).to_string())
pd.set_option("display.width", 250)
print(R[R.k.isin([7, 8])][["method", "k", "half_ari", "temporal_ari", "sil", "auc_mean", "lift_mean"] + [f"auc_{o}" for o in OUTS]].round(3).sort_values(["k", "method"]).to_string(index=False))
