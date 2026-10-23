import time
import pandas as pd
import sqlalchemy
from tt_bank.db.connection import get_engine

t0 = time.time()
print("1. Checking customer_month_ledger.pkl...")
lg = pd.read_pickle("data/processed/phase2_clustering/customer_month_ledger.pkl")
tot_inst = lg["n_inst"].sum()
tot_paid = lg["n_paid"].sum()
tot_late = lg["n_late"].sum()
tot_late30 = lg["n_late30"].sum()
tot_late90 = lg["n_late90"].sum()
tot_unpaid = lg["n_unpaid"].sum()

pct_paid = (tot_paid / tot_inst) * 100
pct_late = (tot_late / tot_inst) * 100
pct_late30 = (tot_late30 / tot_inst) * 100
pct_late90 = (tot_late90 / tot_inst) * 100

print(f"From customer_month_ledger.pkl (1400-1404):")
print(f"Total installments: {tot_inst:,}")
print(f"Paid installments: {tot_paid:,} ({pct_paid:.2f}%) (Claimed: 100%)")
print(f"Late installments: {tot_late:,} ({pct_late:.2f}%) (Claimed: 57.9%)")
print(f"Late > 30 days: {tot_late30:,} ({pct_late30:.2f}%) (Claimed: 29.4%)")
print(f"Late > 90 days: {tot_late90:,} ({pct_late90:.2f}%) (Claimed: 7.2%)")
print(f"Unpaid installments: {tot_unpaid:,}")

# 2. Directly verify from DB for year 1404 (or check unpaid in DB)
print("2. Checking DB directly for unpaid installments and late30 in 1404...")
engine = get_engine()
CD = "LTRIM(RTRIM(REPLACE({c}, CHAR(34), '')))"
dd, pdt = CD.format(c="m.delivery_date"), CD.format(c="m.payed_date")
def ordn(x): return f"(TRY_CAST(LEFT({x},4) AS int)*372 + TRY_CAST(SUBSTRING({x},6,2) AS int)*31 + TRY_CAST(SUBSTRING({x},9,2) AS int))"

q_db = f"""
SELECT 
    COUNT(*) AS total_rows_1404,
    SUM(CASE WHEN LEN({pdt}) >= 10 THEN 1 ELSE 0 END) AS paid_rows_1404,
    SUM(CASE WHEN {pdt} IS NULL OR LEN({pdt}) < 10 THEN 1 ELSE 0 END) AS unpaid_rows_1404,
    SUM(CASE WHEN LEN({pdt}) >= 10 AND {ordn(pdt)} - {ordn(dd)} > 30 THEN 1 ELSE 0 END) AS late30_rows_1404,
    SUM(CASE WHEN LEN({pdt}) >= 10 AND {ordn(pdt)} - {ordn(dd)} > 0 THEN 1 ELSE 0 END) AS late_rows_1404
FROM dbo.Loan_Monthly_Activity m
WHERE {dd} LIKE '1404/%'
"""

with engine.connect() as conn:
    df_db_1404 = pd.read_sql(sqlalchemy.text(q_db), conn)

print("DB 1404 results:")
print(df_db_1404)
tot_1404 = df_db_1404.loc[0, "total_rows_1404"]
paid_1404 = df_db_1404.loc[0, "paid_rows_1404"]
unpaid_1404 = df_db_1404.loc[0, "unpaid_rows_1404"]
late30_1404 = df_db_1404.loc[0, "late30_rows_1404"]
pct_paid_1404 = (paid_1404 / tot_1404) * 100
pct_late30_1404 = (late30_1404 / tot_1404) * 100

print(f"DB 1404 Paid %: {pct_paid_1404:.4f}%")
print(f"DB 1404 Late > 30 days %: {pct_late30_1404:.2f}%")

res = pd.DataFrame([{
    "scope": "1400-1404 (ledger file)",
    "total_inst": tot_inst,
    "paid_share": f"{pct_paid:.2f}%",
    "late30_share": f"{pct_late30:.2f}%",
    "late_share": f"{pct_late:.2f}%",
    "unpaid_count": tot_unpaid
}, {
    "scope": "1404 direct DB",
    "total_inst": tot_1404,
    "paid_share": f"{pct_paid_1404:.2f}%",
    "late30_share": f"{pct_late30_1404:.2f}%",
    "late_share": f"{(df_db_1404.loc[0, 'late_rows_1404'] / tot_1404) * 100:.2f}%",
    "unpaid_count": unpaid_1404
}])
res.to_csv("reports/review_S1_S4/results/v9_ledger_check.csv", index=False)
print("Saved to v9_ledger_check.csv")
