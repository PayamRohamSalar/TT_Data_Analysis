import time
import pandas as pd
from sqlalchemy import text
from tt_bank.db.connection import get_engine
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

engine = get_engine()

q = """
SELECT TOP 10 
    loanfile_id, delivery_date, payed_date, installment_main, installment_interest, installment_penalty,
    Status
FROM dbo.Loan_Monthly_Activity
"""
df = pd.read_sql(q, engine)
print("--- Sample rows from Loan_Monthly_Activity ---")
print(df.to_string())

# Check distinct Status values in Loan_Monthly_Activity
q_status = """
SELECT 
    LTRIM(RTRIM(REPLACE(Status, CHAR(34), ''))) as clean_status,
    COUNT(*) as n_rows
FROM dbo.Loan_Monthly_Activity
GROUP BY LTRIM(RTRIM(REPLACE(Status, CHAR(34), '')))
"""
df_status = pd.read_sql(q_status, engine)
print("\n--- Distinct Status in Loan_Monthly_Activity ---")
print(df_status.to_string())

df_status.to_csv('reports/review_S1_S5b/results/w13_ledger_status_breakdown.csv', index=False)
