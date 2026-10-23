import time
import pandas as pd
import numpy as np

t0 = time.time()
print("Reading features_customer_year.pkl for V15...")
F = pd.read_pickle("data/processed/phase2_clustering/features_customer_year.pkl")
M = F[F.category == "model"]
B = M[M.y == 1403].reset_index(drop=True)
N = F[F.y == 1404].set_index("customer_id")

print(f"1403 Model customers (B): {len(B):,}")
print(f"1404 All customers (N): {len(N):,}")

# Check presence
j = B.customer_id.map(lambda c: c in N.index).to_numpy()
nxt = N.reindex(B.customer_id.to_numpy())
present = j

exit_count = (~present).sum()
exit_rate = exit_count / len(B) * 100
print(f"1403 customers not present in 1404 (exit): {exit_count:,} ({exit_rate:.4f}%)")

# Balances
bal_now = B.bal_dec.fillna(0).to_numpy()
bal_next = nxt.bal_dec.fillna(0).to_numpy()

# 1. loan_uptake
m0 = (B.has_loan_dec.to_numpy() == 0)
y_loan = (nxt.has_loan_dec.fillna(0).to_numpy() == 1) & present
rate_loan = y_loan[m0].mean() * 100
n_m0 = int(m0.sum())
print(f"1. loan_uptake: base n={n_m0:,}, rate={rate_loan:.2f}% (Claimed: 12.3%)")

# 2. balance_halved (nominal)
m1 = bal_now > 0
y_halved = (~present) | (bal_next < 0.5 * bal_now)
rate_halved = y_halved[m1].mean() * 100
n_m1 = int(m1.sum())
print(f"2. balance_halved (nominal): base n={n_m1:,}, rate={rate_halved:.2f}% (Claimed: 31.4%)")

# What if real balance halved (CPI adjusted)?
# In 140312 vs 140412: bal_mean_r or bal_end_r in real terms
bal_now_r = B.bal_end_r.fillna(0).to_numpy()
bal_next_r = nxt.bal_end_r.fillna(0).to_numpy()
m1_r = bal_now_r > 0
y_halved_r = (~present) | (bal_next_r < 0.5 * bal_now_r)
rate_halved_r = y_halved_r[m1_r].mean() * 100
print(f"   balance_halved (REAL / CPI terms): rate={rate_halved_r:.2f}%")

# 3. dormant_next
m2 = np.ones(len(B), bool)
y_dormant = (~present) | (nxt.category.fillna("").to_numpy() == "idle_token") | (nxt.turn_share.fillna(0).to_numpy() < 0.25)
rate_dormant = y_dormant[m2].mean() * 100
n_m2 = int(m2.sum())
print(f"3. dormant_next: base n={n_m2:,}, rate={rate_dormant:.2f}% (Claimed: 8.9%)")

# Component breakdown of dormant_next:
n_exit = (~present).sum()
n_idle = (present & (nxt.category.fillna("").to_numpy() == "idle_token")).sum()
n_low_turn = (present & (nxt.turn_share.fillna(0).to_numpy() < 0.25) & (nxt.category.fillna("").to_numpy() != "idle_token")).sum()
print(f"   dormant breakdown: exit={n_exit:,}, idle_token={n_idle:,}, low_turn (<0.25)={n_low_turn:,}")

# 4. npl_entry
m3 = (B.has_loan_dec.to_numpy() == 1) & (B.npl_share.to_numpy() == 0)
y_npl = present & (nxt.npl_share.fillna(0).to_numpy() > 0)
rate_npl = y_npl[m3].mean() * 100
n_m3 = int(m3.sum())
print(f"4. npl_entry: base n={n_m3:,}, rate={rate_npl:.2f}% (Claimed: 13.5%)")

res_v15 = pd.DataFrame([
    {"outcome": "loan_uptake", "claimed_base": "Non-borrowers", "calculated_base_n": n_m0, "claimed_rate": "12.3%", "calculated_rate": f"{rate_loan:.2f}%"},
    {"outcome": "balance_halved", "claimed_base": "Positive balance", "calculated_base_n": n_m1, "claimed_rate": "31.4%", "calculated_rate": f"{rate_halved:.2f}%"},
    {"outcome": "dormant_next", "claimed_base": "All 1403 model", "calculated_base_n": n_m2, "claimed_rate": "8.9%", "calculated_rate": f"{rate_dormant:.2f}%"},
    {"outcome": "npl_entry", "claimed_base": "Borrowers with 0 NPL", "calculated_base_n": n_m3, "claimed_rate": "13.5%", "calculated_rate": f"{rate_npl:.2f}%"},
    {"outcome": "balance_halved_real", "claimed_base": "Positive real balance", "calculated_base_n": int(m1_r.sum()), "claimed_rate": "N/A (sensitivity)", "calculated_rate": f"{rate_halved_r:.2f}%"},
    {"outcome": "exit_1403_to_1404", "claimed_base": "All 1403 model", "calculated_base_n": len(B), "claimed_rate": "N/A", "calculated_rate": f"{exit_rate:.4f}% ({exit_count} customers)"}
])
res_v15.to_csv("reports/review_S1_S4/results/v15_external_outcomes.csv", index=False)
print("Saved to v15_external_outcomes.csv")
