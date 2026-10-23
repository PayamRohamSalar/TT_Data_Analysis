import sys
sys.stdout.reconfigure(encoding='utf-8')
import time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

t0 = time.time()
print("Reading data for SQ8 (Alternative External Validation Metrics)...")

# 1. Load labels for 1403
lab_m3_k8 = np.load("data/processed/phase2_clustering/s4_labels/M3_k8_B.npy")
lab_m2_k7 = np.load("data/processed/phase2_clustering/s4_labels/M2_k7_B.npy")

# 2. Load features to get 1403 customers and outcomes
F = pd.read_pickle("data/processed/phase2_clustering/features_customer_year.pkl")
B = F[(F.category == "model") & (F.y == 1403)].reset_index(drop=True)
N = F[F.y == 1404].set_index("customer_id")

present = B.customer_id.map(lambda c: c in N.index).to_numpy()
nxt = N.reindex(B.customer_id.to_numpy())

bal_now = B.bal_dec.fillna(0).to_numpy()
bal_next = nxt.bal_dec.fillna(0).to_numpy()

# Define outcomes
OUT = {}
m0 = (B.has_loan_dec.to_numpy() == 0)
OUT["loan_uptake"] = (m0, (nxt.has_loan_dec.fillna(0).to_numpy() == 1) & present)

m1 = bal_now > 0
OUT["balance_halved"] = (m1, (~present) | (bal_next < 0.5 * bal_now))

OUT["dormant_next"] = (np.ones(len(B), bool), (~present) | (nxt.category.fillna("").to_numpy() == "idle_token") | (nxt.turn_share.fillna(0).to_numpy() < 0.25))

m3 = (B.has_loan_dec.to_numpy() == 1) & (B.npl_share.to_numpy() == 0)
OUT["npl_entry"] = (m3, present & (nxt.npl_share.fillna(0).to_numpy() > 0))

def evaluate_method_outcomes(method_name, labels):
    records = []
    for out_name, (mask, y_raw) in OUT.items():
        y = y_raw[mask].astype(float)
        l = labels[mask]
        n = len(y)
        k_clusters = len(np.unique(l))
        base_rate = float(y.mean())
        
        # Cluster means
        cluster_means = pd.Series(y).groupby(l).mean()
        cluster_counts = pd.Series(y).groupby(l).count()
        
        # Predicted probability for each individual
        y_prob = pd.Series(l).map(cluster_means).to_numpy()
        
        # 1. ROC AUC
        auc = float(roc_auc_score(y, y_prob)) if len(np.unique(y)) > 1 else np.nan
        
        # 2. Top cluster lift
        max_c_rate = float(cluster_means.max())
        top_cluster_lift = max_c_rate / base_rate if base_rate > 0 else np.nan
        
        # 3. Decile top 10% lift
        # Sort by predicted probability descending
        order = np.argsort(-y_prob)
        top_10_pct_n = int(0.1 * n)
        top_10_rate = float(y[order[:top_10_pct_n]].mean())
        decile_1_lift = top_10_rate / base_rate if base_rate > 0 else np.nan
        
        # 4. Adjusted R2 (as defined in S4)
        sst = ((y - y.mean()) ** 2).sum()
        ssb = (cluster_counts * (cluster_means - y.mean()) ** 2).sum()
        r2 = ssb / sst if sst > 0 else 0
        adj_r2 = float(1 - (1 - r2) * (n - 1) / (n - k_clusters))
        
        records.append({
            "method": method_name,
            "outcome": out_name,
            "base_n": n,
            "base_rate_pct": base_rate * 100,
            "adj_r2": adj_r2,
            "roc_auc": auc,
            "top_cluster_lift": top_cluster_lift,
            "decile_1_lift": decile_1_lift
        })
    return records

res_m3 = evaluate_method_outcomes("M3 (k=8)", lab_m3_k8)
res_m2 = evaluate_method_outcomes("M2 (k=7)", lab_m2_k7)

df_eval = pd.DataFrame(res_m3 + res_m2)
print("\n--- Comparison of External Validation Metrics: M3 (k=8) vs M2 (k=7) ---")
print(df_eval.to_string(index=False))

# Pivot for side-by-side comparison
pivot_auc = df_eval.pivot(index="outcome", columns="method", values="roc_auc")
pivot_r2 = df_eval.pivot(index="outcome", columns="method", values="adj_r2")
pivot_top_lift = df_eval.pivot(index="outcome", columns="method", values="top_cluster_lift")
pivot_dec_lift = df_eval.pivot(index="outcome", columns="method", values="decile_1_lift")

print("\n--- ROC AUC: M3 (k=8) vs M2 (k=7) ---")
print(pivot_auc.round(4))

print("\n--- Adjusted R2: M3 (k=8) vs M2 (k=7) ---")
print(pivot_r2.round(4))

print("\n--- Top Cluster Lift: M3 (k=8) vs M2 (k=7) ---")
print(pivot_top_lift.round(2))

print("\n--- Decile 1 Lift: M3 (k=8) vs M2 (k=7) ---")
print(pivot_dec_lift.round(2))

df_eval.to_csv("reports/review_S1_S4/results/sq08_alternative_metrics.csv", index=False)
print("\nSaved SQ8 results to sq08_alternative_metrics.csv")
