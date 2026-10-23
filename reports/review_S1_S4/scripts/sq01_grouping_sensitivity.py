import sys
sys.stdout.reconfigure(encoding='utf-8')
import time
import pandas as pd
import numpy as np

t0 = time.time()
print("Reading panel_customer_year.pkl for Special Question 1...")
pan = pd.read_pickle("data/processed/phase2_clustering/panel_customer_year.pkl")
pan_1404 = pan[pan["y"] == 1404].copy()

total_cust_1404 = len(pan_1404)
total_bal_mean_1404 = pan_1404["bal_mean"].sum()
total_bal_dec_1404 = pan_1404["bal_dec"].sum()

# 1. Institutional threshold sensitivity: 20, 50, 100, 200
thresholds = [20, 50, 100, 200]
inst_sens = []
for th in thresholds:
    inst_sub = pan_1404[pan_1404["nacc_max"] >= th]
    n_c = len(inst_sub)
    share_c = (n_c / total_cust_1404) * 100
    b_mean = inst_sub["bal_mean"].sum()
    share_b_mean = (b_mean / total_bal_mean_1404) * 100
    b_dec = inst_sub["bal_dec"].sum()
    share_b_dec = (b_dec / total_bal_dec_1404) * 100
    
    inst_sens.append({
        "threshold_nacc_max": th,
        "customer_count": n_c,
        "customer_share_pct": share_c,
        "bal_mean_hemmat": b_mean / 1e13,
        "bal_mean_share_pct": share_b_mean,
        "bal_dec_hemmat": b_dec / 1e13,
        "bal_dec_share_pct": share_b_dec
    })

df_inst = pd.DataFrame(inst_sens)
print("\n--- Institutional Threshold Sensitivity in 1404 ---")
print(df_inst.to_string(index=False))

# 2. Loan customers forced into "model" with tiny deposit balance
# Criteria for idle: months >= 6 and (turn_months < 3 or bal_max < 5_000_000)
# How many of these have has_primary_loan == True?
mod_1404 = pan_1404[pan_1404["category"] == "model"]
loan_in_model = mod_1404[mod_1404["has_primary_loan"] == True]

tiny_deposit_borrowers = loan_in_model[(loan_in_model["turn_months"] < 3) | (loan_in_model["bal_max"] < 5_000_000)]
n_tiny = len(tiny_deposit_borrowers)
pct_of_borrowers = (n_tiny / len(loan_in_model)) * 100
pct_of_model = (n_tiny / len(mod_1404)) * 100

print(f"\n--- Borrowers in Model with Tiny/Idle Deposit Behavior ---")
print(f"Total borrowers in Model group: {len(loan_in_model):,}")
print(f"Borrowers with (turn_months < 3 OR bal_max < 5M Rials): {n_tiny:,} ({pct_of_borrowers:.2f}% of borrowers, {pct_of_model:.2f}% of all model)")
print(f"Their median bal_mean: {tiny_deposit_borrowers['bal_mean'].median():,.0f} Rials")
print(f"Their median bal_dec: {tiny_deposit_borrowers['bal_dec'].median():,.0f} Rials")
print(f"Their median primary loan balance: {tiny_deposit_borrowers['bal_primary'].median():,.0f} Rials")

# 3. Newcomers (نوپا)
newcomers = pan_1404[pan_1404["category"] == "newcomer"]
print(f"\n--- Newcomers (نوپا) in 1404 ---")
print(f"Total newcomers: {len(newcomers):,}")
print(f"Distribution of first_ym among newcomers:")
print(newcomers["first_ym"].value_counts().sort_index())
print(f"Distribution of months observed among newcomers:")
print(newcomers["months"].value_counts().sort_index())

# Partial other
partial_other = pan_1404[pan_1404["category"] == "partial_other"]
print(f"\nPartial other count: {len(partial_other)}")
if not partial_other.empty:
    print(partial_other[["customer_id", "first_ym", "last_ym", "months", "turn_months", "bal_mean", "has_primary_loan"]])

# Save results
df_inst.to_csv("reports/review_S1_S4/results/sq01_institutional_sensitivity.csv", index=False)
pd.DataFrame([{
    "metric": "Borrowers in model with tiny deposit",
    "count": n_tiny,
    "share_of_model_borrowers_pct": pct_of_borrowers,
    "share_of_all_model_pct": pct_of_model,
    "median_bal_mean_rial": float(tiny_deposit_borrowers['bal_mean'].median()),
    "median_bal_primary_loan_rial": float(tiny_deposit_borrowers['bal_primary'].median())
}]).to_csv("reports/review_S1_S4/results/sq01_tiny_deposit_borrowers.csv", index=False)
print("Saved SQ1 results to results/")
