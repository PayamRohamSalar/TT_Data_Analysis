import pandas as pd
import numpy as np

print("Loading s4_scorecard_full.csv and s4_method_ranking.csv...")
full_sc = pd.read_csv("data/processed/phase2_clustering/s4_scorecard_full.csv")
official_rank = pd.read_csv("data/processed/phase2_clustering/s4_method_ranking.csv")

print("Official ranking:")
print(official_rank)

# Exact logic from 23_s4_scorecard.py
def score_frame(R_, w):
    rows = []
    for k, g in R_.groupby("k"):
        if len(g) < 2: continue
        sc = pd.DataFrame(index=g.index)
        def rk(col, high=True):
            r = g[col].rank(ascending=not high, method="average", na_option="keep")
            return 1 - (r - 1) / (r.max() - 1) if r.max() > 1 else r * 0 + 0.5
        internal = pd.concat([rk("sil"), rk("ch"), rk("db", high=False)], axis=1).mean(axis=1)
        stability = pd.concat([rk("half_ari"), rk("temporal_ari")], axis=1).mean(axis=1)
        external = rk("ext")
        usability = pd.concat([rk("entropy"), rk("min_share"), rk("fidelity")], axis=1).mean(axis=1)
        comp = (w["internal"] * internal.fillna(internal.mean()) + 
                w["stability"] * stability.fillna(0.3) + 
                w["external"] * external.fillna(0) + 
                w["usability"] * usability.fillna(0.5))
        for idx in g.index:
            rows.append(dict(method=g.loc[idx, "method"], k=k, 
                             internal=internal[idx], stability=stability[idx], 
                             external=external[idx], usability=usability[idx], 
                             composite=comp[idx]))
    return pd.DataFrame(rows)

W = {"base": dict(internal=.25, stability=.30, external=.30, usability=.15),
     "equal": dict(internal=.25, stability=.25, external=.25, usability=.25),
     "external_heavy": dict(internal=.15, stability=.25, external=.45, usability=.15)}

S = {n: score_frame(full_sc, w) for n, w in W.items()}
rank_reproduced = pd.DataFrame({n: s.groupby("method").composite.mean() for n, s in S.items()})
rank_reproduced["rank_base"] = rank_reproduced.base.rank(ascending=False)
rank_reproduced["rank_equal"] = rank_reproduced.equal.rank(ascending=False)
rank_reproduced["rank_ext"] = rank_reproduced.external_heavy.rank(ascending=False)
rank_reproduced["borda"] = rank_reproduced[["rank_base", "rank_equal", "rank_ext"]].mean(axis=1)
rank_reproduced = rank_reproduced.sort_values("borda")

print("\nReproduced ranking:")
print(rank_reproduced.round(3))

# Compare reproduced with official
comp_rank = rank_reproduced.reset_index().merge(official_rank, on="method", suffixes=("_calc", "_official"))
print("\nComparison:")
print(comp_rank[["method", "base_official", "base_calc", "rank_base_official", "rank_base_calc", "borda_official", "borda_calc"]])

# Now investigate WHY M2 is #1:
# Let's break down M2 vs M3 across the 4 pillars at k=7 and k=8
print("\nBreakdown of pillar scores by method (across k in base weighting):")
s_base = S["base"]
pillar_summary = s_base.groupby("method")[["internal", "stability", "external", "usability", "composite"]].mean()
print(pillar_summary.round(3).sort_values("composite", ascending=False))

# Sensitivity 1: What if we use raw values min-max normalized across all methods (not within-k rank)?
def minmax(s, high=True):
    val = s.to_numpy()
    if not high: val = -val
    mn, mx = np.nanmin(val), np.nanmax(val)
    return (val - mn) / (mx - mn) if mx > mn else np.full_like(val, 0.5)

raw_df = full_sc[full_sc["k"].isin([5, 6, 7, 8, 9])].copy()
raw_internal = (minmax(raw_df["sil"]) + minmax(raw_df["ch"]) + minmax(raw_df["db"], high=False)) / 3.0
raw_stability = (minmax(raw_df["half_ari"]) + minmax(raw_df["temporal_ari"])) / 2.0
raw_external = minmax(raw_df["ext"])
raw_usability = (minmax(raw_df["entropy"]) + minmax(raw_df["min_share"]) + minmax(raw_df["fidelity"])) / 3.0

raw_comp = 0.25 * pd.Series(raw_internal).fillna(np.nanmean(raw_internal)) + \
           0.30 * pd.Series(raw_stability).fillna(0.3) + \
           0.30 * pd.Series(raw_external).fillna(0.0) + \
           0.15 * pd.Series(raw_usability).fillna(0.5)

raw_df["raw_composite"] = raw_comp.values
raw_ranking = raw_df.groupby("method")["raw_composite"].mean().sort_values(ascending=False)
print("\nAlternative Ranking using global min-max normalization:")
print(raw_ranking.round(3))

# Save results
comp_rank.to_csv("reports/review_S1_S4/results/v17_ranking_comparison.csv", index=False)
pillar_summary.to_csv("reports/review_S1_S4/results/v17_pillar_summary.csv")
raw_ranking.to_csv("reports/review_S1_S4/results/v17_raw_normalization_ranking.csv")
print("Saved V17 results to results/")
