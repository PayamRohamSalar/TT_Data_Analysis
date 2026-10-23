import time
import pandas as pd
import numpy as np

t0 = time.time()
print("Reading features_customer_year.pkl...")
feat = pd.read_pickle("data/processed/phase2_clustering/features_customer_year.pkl")
print(f"Loaded features_customer_year.pkl: {feat.shape} in {time.time()-t0:.1f}s")

# 1. Key uniqueness
n_rows = len(feat)
n_unique_keys = len(feat.groupby(["customer_id", "y"]))
key_unique = (n_rows == n_unique_keys)
print(f"Key (customer_id, y) unique? {key_unique} ({n_unique_keys:,} / {n_rows:,})")

# 2. Check ranges of bounded features
bounded_cols = ["flow_ratio", "turn_share", "drawdown", "npl_share"]
range_stats = []
for c in bounded_cols:
    if c in feat.columns:
        s = feat[c]
        c_min = s.min()
        c_max = s.max()
        c_null = s.isna().sum()
        in_0_1 = (c_min >= 0.0) and (c_max <= 1.0000001) and (c_null == 0)
        print(f"Feature '{c}': min={c_min}, max={c_max}, nulls={c_null}, in [0,1]? {in_0_1}")
        range_stats.append({
            "feature": c,
            "min": c_min,
            "max": c_max,
            "nulls": c_null,
            "is_valid_range": in_0_1
        })
    else:
        print(f"Feature '{c}' NOT found in columns!")

# 3. Sum of account type shares
# Account share columns
type_cols = ["share_long_k", "share_short_k", "share_qard_k", "share_current_k", "share_special_k"]
found_type_cols = [c for c in type_cols if c in feat.columns]
print(f"Found account type share columns: {found_type_cols}")

if len(found_type_cols) == 5:
    type_sum = feat[found_type_cols].sum(axis=1)
    # Check for rows that have non-zero deposit balance or have account type info
    # In S2: "مجموع سهم نوع حساب: 1.000 برای 99.97٪ ردیف‌های دارای مانده"
    has_type = type_sum > 0
    # For rows where has_type is true, how close to 1.0 is it?
    close_to_1 = np.isclose(type_sum[has_type], 1.0, atol=1e-3).mean() * 100
    print(f"Account type shares: rows with sum > 0 = {has_type.sum():,}")
    print(f"Of those with sum > 0, % summing to 1.0 (+/-0.001): {close_to_1:.2f}%")
    print(f"Quantiles of type_sum[has_type]: min={type_sum[has_type].min()}, p50={type_sum[has_type].median()}, max={type_sum[has_type].max()}")

# 4. Sum of loan_dec_r in 1404
feat_1404 = feat[feat["y"] == 1404]
if "loan_dec_r" in feat_1404.columns:
    sum_loan_1404 = feat_1404["loan_dec_r"].sum()
    sum_loan_1404_hemmat = sum_loan_1404 / 1e13
    print(f"Sum of loan_dec_r in 1404: {sum_loan_1404:,.0f} Rials = {sum_loan_1404_hemmat:.2f} Hemmat (Claimed: 124.97 Hemmat)")
else:
    print("loan_dec_r column not found!")
    sum_loan_1404_hemmat = None

res_v13 = pd.DataFrame([
    {"metric": "Key (customer_id, y) unique", "claimed": "True", "calculated": str(key_unique)},
    {"metric": "flow_ratio range [0, 1]", "claimed": "[0, 1]", "calculated": f"[{feat['flow_ratio'].min():.4f}, {feat['flow_ratio'].max():.4f}]"},
    {"metric": "turn_share range [0, 1]", "claimed": "[0, 1]", "calculated": f"[{feat['turn_share'].min():.4f}, {feat['turn_share'].max():.4f}]"},
    {"metric": "drawdown range [0, 1]", "claimed": "[0, 1]", "calculated": f"[{feat['drawdown'].min():.4f}, {feat['drawdown'].max():.4f}]"},
    {"metric": "npl_share range [0, 1]", "claimed": "[0, 1]", "calculated": f"[{feat['npl_share'].min():.4f}, {feat['npl_share'].max():.4f}]"},
    {"metric": "Sum of account type shares close to 1.0", "claimed": "1.000 for 99.97%", "calculated": f"{close_to_1:.2f}%"},
    {"metric": "Sum of loan_dec_r in 1404 (Hemmat)", "claimed": "124.97", "calculated": f"{sum_loan_1404_hemmat:.2f}"},
])
res_v13.to_csv("reports/review_S1_S4/results/v13_features_recalc.csv", index=False)
print("Saved to v13_features_recalc.csv")
