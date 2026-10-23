import time
import pandas as pd
import numpy as np

t0 = time.time()
print("Reading panel_customer_year.pkl...")
pan = pd.read_pickle("data/processed/phase2_clustering/panel_customer_year.pkl")
print(f"Loaded {len(pan):,} rows in {time.time()-t0:.1f}s")

# 1. Check uniqueness of (customer_id, y)
n_rows = len(pan)
n_unique_keys = len(pan.groupby(["customer_id", "y"]))
is_key_unique = (n_rows == n_unique_keys)
print(f"Key (customer_id, y) unique? {is_key_unique} ({n_unique_keys:,} / {n_rows:,})")

# 2. Group counts in 1404
pan_1404 = pan[pan["y"] == 1404]
cat_1404 = pan_1404["category"].value_counts()
print("\nGroup counts in 1404:")
print(cat_1404)

model_count = cat_1404.get("model", 0)
idle_count = cat_1404.get("idle_token", 0)
new_count = cat_1404.get("newcomer", 0)
inst_count = cat_1404.get("institutional_candidate", 0)
other_count = cat_1404.get("partial_other", 0)
total_1404 = len(pan_1404)

print(f"\n1404 Detailed counts:")
print(f"Model: {model_count:,} (Claimed: 636,016)")
print(f"Idle: {idle_count:,} (Claimed: 66,191)")
print(f"Newcomer: {new_count:,} (Claimed: 10,126)")
print(f"Institutional: {inst_count:,} (Claimed: 574)")
print(f"Other: {other_count:,} (Claimed: 1)")
print(f"Total 1404: {total_1404:,} (Claimed: 712,908)")

# 3. Control totals: sum of bal_dec each year
yearly_bal = pan.groupby("y")["bal_dec"].sum() / 1e13
print("\nSum of bal_dec by year (Hemmat = 1e13 Rials):")
for y, b in yearly_bal.items():
    print(f"Year {y}: {b:.2f} Hemmat")

claimed_bal = {1400: 24.81, 1401: 32.75, 1402: 47.27, 1403: 63.96, 1404: 84.77}
bal_diffs = {y: f"{yearly_bal.loc[y]:.2f} (diff: {yearly_bal.loc[y] - claimed_bal[y]:.4f})" for y in claimed_bal}

res_v12 = pd.DataFrame([
    {"metric": "Key (customer_id, y) unique", "claimed": "True", "calculated": str(is_key_unique)},
    {"metric": "1404 Model count", "claimed": "636,016", "calculated": str(model_count)},
    {"metric": "1404 Idle count", "claimed": "66,191", "calculated": str(idle_count)},
    {"metric": "1404 Newcomer count", "claimed": "10,126", "calculated": str(new_count)},
    {"metric": "1404 Institutional count", "claimed": "574", "calculated": str(inst_count)},
    {"metric": "1404 Partial other count", "claimed": "1", "calculated": str(other_count)},
    {"metric": "1404 Total", "claimed": "712,908", "calculated": str(total_1404)},
    {"metric": "bal_dec 1400 (Hemmat)", "claimed": "24.81", "calculated": f"{yearly_bal.loc[1400]:.2f}"},
    {"metric": "bal_dec 1401 (Hemmat)", "claimed": "32.75", "calculated": f"{yearly_bal.loc[1401]:.2f}"},
    {"metric": "bal_dec 1402 (Hemmat)", "claimed": "47.27", "calculated": f"{yearly_bal.loc[1402]:.2f}"},
    {"metric": "bal_dec 1403 (Hemmat)", "claimed": "63.96", "calculated": f"{yearly_bal.loc[1403]:.2f}"},
    {"metric": "bal_dec 1404 (Hemmat)", "claimed": "84.77", "calculated": f"{yearly_bal.loc[1404]:.2f}"},
])
res_v12.to_csv("reports/review_S1_S4/results/v12_panel_recalc.csv", index=False)
print("Saved to v12_panel_recalc.csv")
