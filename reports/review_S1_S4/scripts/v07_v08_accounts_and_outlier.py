import pandas as pd
import sqlalchemy
from tt_bank.db.connection import get_engine

engine = get_engine()

# V8: Query DB for customer 186027389
print("Querying DB for customer 186027389 across all months...")
with engine.connect() as conn:
    q_v8 = """
    SELECT year_mount, COUNT(*) AS n_accounts, 
           SUM(avr_total_amount_eq) AS bal,
           MAX(avr_total_amount_eq) AS max_acc_bal,
           MIN(avr_total_amount_eq) AS min_acc_bal
    FROM dbo.Deposit_Monthly_Activity
    WHERE customer_id = 186027389
    GROUP BY year_mount
    ORDER BY year_mount
    """
    df_v8 = pd.read_sql(sqlalchemy.text(q_v8), conn)

print("V8 results for customer 186027389:")
print(df_v8)
df_v8.to_csv("reports/review_S1_S4/results/v8_customer_186027389_monthly.csv", index=False)

# Check last appearance month
if not df_v8.empty:
    last_ym = df_v8["year_mount"].max()
    min_acc = df_v8["n_accounts"].min()
    max_acc = df_v8["n_accounts"].max()
    print(f"Customer 186027389: account range [{min_acc:,}, {max_acc:,}], last month present: {last_ym}")

# V7: Check from panel_customer_year.pkl and customer_month_deposit.pkl
print("Loading panel_customer_year.pkl to verify V7...")
pan = pd.read_pickle("data/processed/phase2_clustering/panel_customer_year.pkl")
pan_1404 = pan[pan["y"] == 1404].copy()

# Inst candidates (nacc_max >= 100 in 1404)
inst_1404 = pan_1404[pan_1404["nacc_max"] >= 100]
n_inst = len(inst_1404)
# Balance share of average balance
total_bal_mean = pan_1404["bal_mean"].sum()
inst_bal_mean = inst_1404["bal_mean"].sum()
inst_share = (inst_bal_mean / total_bal_mean) * 100

print(f"V7: Institutional customers in 1404 (nacc_max >= 100): {n_inst} (Claimed: 574)")
print(f"V7: Share of average balance: {inst_share:.2f}% (Claimed: 21.0%)")

# Check category column in panel
cat_counts = pan_1404["category"].value_counts()
print("Category counts in 1404:")
print(cat_counts)

res_v7 = pd.DataFrame([{
    "metric": "V7 Institutional Customers (1404)",
    "claimed": "574",
    "calculated": str(n_inst),
    "diff": n_inst - 574
}, {
    "metric": "V7 Share of Average Balance (%)",
    "claimed": "21.0%",
    "calculated": f"{inst_share:.2f}%",
    "diff": f"{inst_share - 21.0:.2f}%"
}])
res_v7.to_csv("reports/review_S1_S4/results/v7_institutional_1404.csv", index=False)
