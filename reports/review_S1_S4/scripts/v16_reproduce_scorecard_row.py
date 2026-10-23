import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier

sys.path.insert(0, str(Path.cwd() / "src"))
from tt_bank.phase2_clustering.prep import Prep

t0 = time.time()
print("Reading s4_scorecard_full.csv...")
full_sc = pd.read_csv("data/processed/phase2_clustering/s4_scorecard_full.csv")
row_m3_k8 = full_sc[(full_sc["method"] == "M3") & (full_sc["k"] == 8)].iloc[0]

print("Claimed values in s4_scorecard_full.csv for M3 k=8:")
print(f"min_share: {row_m3_k8['min_share']:.6f}")
print(f"entropy: {row_m3_k8['entropy']:.6f}")
print(f"temporal_ari: {row_m3_k8['temporal_ari']:.6f}")
print(f"half_ari: {row_m3_k8['half_ari']:.6f}")
print(f"adjr2_dormant_next: {row_m3_k8['adjr2_dormant_next']:.6f}")
print(f"lift_dormant_next: {row_m3_k8['lift_dormant_next']:.6f}")
print(f"fidelity: {row_m3_k8['fidelity']:.6f}")
print(f"ext (mean adjr2): {row_m3_k8['ext']:.6f}")

# 1. Load labels A and B
lab_A = np.load("data/processed/phase2_clustering/s4_labels/M3_k8_A.npy")
lab_B = np.load("data/processed/phase2_clustering/s4_labels/M3_k8_B.npy")

print(f"\nLoaded M3_k8_A: {len(lab_A):,} labels, unique: {np.unique(lab_A)}")
print(f"Loaded M3_k8_B: {len(lab_B):,} labels, unique: {np.unique(lab_B)}")

# Cluster sizes in Year A (1404)
counts_A = pd.Series(lab_A).value_counts().sort_index()
shares_A = counts_A / len(lab_A)
print("\nCluster sizes Year A (1404):")
for c, (cnt, sh) in enumerate(zip(counts_A, shares_A)):
    print(f"Cluster {c}: {cnt:,} ({sh*100:.2f}%)")

min_sh_calc = float(shares_A.min())
# Entropy
p_ = shares_A.to_numpy()
ent_calc = float(-(p_ * np.log(p_)).sum() / np.log(len(p_)))
print(f"\nRecalculated min_share: {min_sh_calc:.6f} (Claimed: {row_m3_k8['min_share']:.6f})")
print(f"Recalculated entropy: {ent_calc:.6f} (Claimed: {row_m3_k8['entropy']:.6f})")

# 2. Recalculate adjr2 for dormant_next on Year B (1403)
F = pd.read_pickle("data/processed/phase2_clustering/features_customer_year.pkl")
B = F[(F.category == "model") & (F.y == 1403)].reset_index(drop=True)
N = F[F.y == 1404].set_index("customer_id")
present = B.customer_id.map(lambda c: c in N.index).to_numpy()
nxt = N.reindex(B.customer_id.to_numpy())

# dormant_next definition
m_dormant = np.ones(len(B), bool)
y_dormant = (~present) | (nxt.category.fillna("").to_numpy() == "idle_token") | (nxt.turn_share.fillna(0).to_numpy() < 0.25)

def calc_adjr2(y, lab, mask):
    y_m = y[mask].astype(float)
    l_m = lab[mask]
    g = pd.Series(y_m).groupby(l_m).agg(["mean", "count"])
    sst = ((y_m - y_m.mean()) ** 2).sum()
    ssb = (g["count"] * (g["mean"] - y_m.mean()) ** 2).sum()
    r2 = ssb / sst if sst > 0 else 0
    n_, k_ = len(y_m), len(g)
    return float(1 - (1 - r2) * (n_ - 1) / (n_ - k_)), g

adjr2_dormant_calc, g_dormant = calc_adjr2(y_dormant, lab_B, m_dormant)
lift_dormant_calc = float(g_dormant["mean"].max() / y_dormant.mean())

print(f"\nRecalculated adjr2_dormant_next: {adjr2_dormant_calc:.6f} (Claimed: {row_m3_k8['adjr2_dormant_next']:.6f})")
print(f"Recalculated lift_dormant_next: {lift_dormant_calc:.6f} (Claimed: {row_m3_k8['lift_dormant_next']:.6f})")

# 3. Recalculate tree fidelity
A = F[(F.category == "model") & (F.y == 1404)].reset_index(drop=True)
prep = Prep.from_json("data/processed/phase2_clustering/prep_spec.json")
XA = prep.transform(A)

rng = np.random.default_rng(0)
idx = rng.permutation(len(XA))
tr, te = idx[: int(0.6 * len(XA))], idx[int(0.6 * len(XA)):]
dt = DecisionTreeClassifier(max_depth=4, random_state=0).fit(XA[tr], lab_A[tr])
fidelity_calc = float((dt.predict(XA[te]) == lab_A[te]).mean())

print(f"\nRecalculated tree fidelity: {fidelity_calc:.6f} (Claimed: {row_m3_k8['fidelity']:.6f})")

res_v16 = pd.DataFrame([{
    "metric": "min_share",
    "claimed": f"{row_m3_k8['min_share']:.6f}",
    "calculated": f"{min_sh_calc:.6f}",
    "diff": f"{abs(min_sh_calc - row_m3_k8['min_share']):.2e}"
}, {
    "metric": "entropy",
    "claimed": f"{row_m3_k8['entropy']:.6f}",
    "calculated": f"{ent_calc:.6f}",
    "diff": f"{abs(ent_calc - row_m3_k8['entropy']):.2e}"
}, {
    "metric": "adjr2_dormant_next",
    "claimed": f"{row_m3_k8['adjr2_dormant_next']:.6f}",
    "calculated": f"{adjr2_dormant_calc:.6f}",
    "diff": f"{abs(adjr2_dormant_calc - row_m3_k8['adjr2_dormant_next']):.2e}"
}, {
    "metric": "lift_dormant_next",
    "claimed": f"{row_m3_k8['lift_dormant_next']:.6f}",
    "calculated": f"{lift_dormant_calc:.6f}",
    "diff": f"{abs(lift_dormant_calc - row_m3_k8['lift_dormant_next']):.2e}"
}, {
    "metric": "tree_fidelity",
    "claimed": f"{row_m3_k8['fidelity']:.6f}",
    "calculated": f"{fidelity_calc:.6f}",
    "diff": f"{abs(fidelity_calc - row_m3_k8['fidelity']):.2e}"
}])
res_v16.to_csv("reports/review_S1_S4/results/v16_scorecard_m3_k8_recalc.csv", index=False)
print("Saved to v16_scorecard_m3_k8_recalc.csv")
