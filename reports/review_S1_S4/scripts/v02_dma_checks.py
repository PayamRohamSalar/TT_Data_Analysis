import pandas as pd
import sqlalchemy
from tt_bank.db.connection import get_engine

# 1. From dma_duplicate_check.csv and dma_null_customer_check.csv
dup_df = pd.read_csv("data/processed/phase2_clustering/dma_duplicate_check.csv")
null_df = pd.read_csv("data/processed/phase2_clustering/dma_null_customer_check.csv")

total_raw = dup_df["raw_rows"].sum()
total_unique = dup_df["unique_account_rows"].sum()
diff_dup = total_raw - total_unique
total_null = null_df["null_customer_account_rows"].sum()
total_null_bal = null_df["null_customer_balance"].sum()

print(f"File summary:")
print(f"Total raw rows: {total_raw}")
print(f"Total unique account rows: {total_unique}")
print(f"Total duplicate rows: {diff_dup}")
print(f"Total null customer account rows: {total_null}")
print(f"Total null customer balance: {total_null_bal}")

# 2. Check directly from DB for the null rows count
engine = get_engine()
with engine.connect() as conn:
    print("Checking DB for total rows and null customer_id...")
    # Fast query: count nulls in Deposit_Monthly_Activity
    q_null = "SELECT COUNT(*) AS null_cnt, SUM(avr_total_amount_eq) AS null_bal FROM dbo.Deposit_Monthly_Activity WHERE customer_id IS NULL"
    res_null = conn.execute(sqlalchemy.text(q_null)).fetchone()
    print(f"DB null customer_id rows: {res_null[0]}, balance: {res_null[1]}")

res_df = pd.DataFrame([{
    "claimed_raw_rows": 113396202,
    "found_raw_rows": total_raw,
    "claimed_duplicates": 928,
    "found_duplicates": diff_dup,
    "claimed_null_customer_rows": 118,
    "found_null_customer_rows_file": total_null,
    "found_null_customer_rows_db": res_null[0],
    "null_balance_rial": res_null[1]
}])
res_df.to_csv("reports/review_S1_S4/results/v2_dma_duplicates_nulls.csv", index=False)
print("Saved to v2_dma_duplicates_nulls.csv")
