import time
import pandas as pd
import sqlalchemy
from tt_bank.db.connection import get_engine

t0 = time.time()
engine = get_engine()

# V1: 12/1404 deposit balance and customer count
query_v1 = """
SELECT 
    COUNT(DISTINCT customer_id) AS distinct_customers,
    COUNT(*) AS total_account_rows,
    SUM(bal) AS total_balance_rial,
    SUM(bal) / 1e13 AS total_balance_hemmat
FROM (
    SELECT customer_id, deposit_id, MAX(avr_total_amount_eq) AS bal
    FROM dbo.Deposit_Monthly_Activity
    WHERE year_mount = 140412 AND customer_id IS NOT NULL
    GROUP BY customer_id, deposit_id
) a
"""

print("Running V1 query on DB...")
with engine.connect() as conn:
    df_v1 = pd.read_sql(sqlalchemy.text(query_v1), conn)

df_v1.to_csv("reports/review_S1_S4/results/v1_deposit_140412.csv", index=False)
print("V1 Results:")
print(df_v1)
print(f"Time taken: {time.time() - t0:.1f}s")
