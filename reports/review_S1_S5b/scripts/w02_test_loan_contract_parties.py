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

t0 = time.time()
engine = get_engine()

# Let's check 140412 contracts
q = """
WITH ContractParties AS (
    SELECT 
        loanfile_id, 
        COUNT(DISTINCT customer_id) as n_parties,
        MIN(customer_id) as min_cust,
        MAX(customer_id) as max_cust
    FROM dbo.Loan_Remain
    WHERE Transaction_Date BETWEEN 14041201 AND 14041231
    GROUP BY loanfile_id
)
SELECT 
    cp.n_parties,
    COUNT(*) as n_contracts,
    SUM(CASE WHEN c.loanfile_id IS NOT NULL THEN 1 ELSE 0 END) as n_with_contract_info,
    SUM(CASE WHEN c.loanfile_id IS NOT NULL AND cp.n_parties = 1 AND cp.min_cust = c.main_customer_id THEN 1 ELSE 0 END) as n_single_match,
    SUM(CASE WHEN c.loanfile_id IS NOT NULL AND cp.n_parties = 1 AND cp.min_cust <> c.main_customer_id THEN 1 ELSE 0 END) as n_single_mismatch
FROM ContractParties cp
LEFT JOIN dbo.vw_Loan_Contract_Dedup c ON c.loanfile_id = cp.loanfile_id
GROUP BY cp.n_parties
ORDER BY cp.n_parties
"""

print("Running query for 140412...")
df = pd.read_sql(q, engine)
print(f"Elapsed: {time.time()-t0:.1f}s")
print(df)
df.to_csv('reports/review_S1_S5b/results/w02_loan_contract_parties_140412.csv', index=False)
