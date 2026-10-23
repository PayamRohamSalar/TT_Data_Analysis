import time
import pandas as pd
import sqlalchemy
from tt_bank.db.connection import get_engine

t0 = time.time()
engine = get_engine()

print("1. Checking V10: Account type coverage in 12/1404...")
q_v10 = """
SELECT 
    COUNT(*) AS total_accounts,
    SUM(bal) AS total_balance,
    SUM(CASE WHEN a.deposit_id IS NULL THEN 1 ELSE 0 END) AS no_type_accounts,
    SUM(CASE WHEN a.deposit_id IS NULL THEN bal ELSE 0 END) AS no_type_balance,
    CAST(SUM(CASE WHEN a.deposit_id IS NULL THEN 1 ELSE 0 END) AS float) / COUNT(*) * 100 AS pct_no_type_accounts,
    CAST(SUM(CASE WHEN a.deposit_id IS NULL THEN bal ELSE 0 END) AS float) / SUM(bal) * 100 AS pct_no_type_balance
FROM (
    SELECT deposit_id, MAX(avr_total_amount_eq) AS bal
    FROM dbo.Deposit_Monthly_Activity
    WHERE year_mount = 140412
    GROUP BY deposit_id
) d
LEFT JOIN dbo.vw_Deposit_Account_Dedup a ON a.deposit_id = d.deposit_id
"""

with engine.connect() as conn:
    df_v10 = pd.read_sql(sqlalchemy.text(q_v10), conn)

print("V10 results:")
print(df_v10)
df_v10.to_csv("reports/review_S1_S4/results/v10_account_type_coverage_140412.csv", index=False)

print("\n2. Checking V11: Customer_Profile mapping...")
# First inspect Customer_Profile schema
with engine.connect() as conn:
    # Get column names of Customer_Profile
    cols_prof = [r[0] for r in conn.execute(sqlalchemy.text("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='Customer_Profile'")).fetchall()]
    print("Customer_Profile columns:", cols_prof)

    # Count total customers in Customer_Profile
    total_prof = conn.execute(sqlalchemy.text("SELECT COUNT(DISTINCT Customer_Id) FROM dbo.Customer_Profile")).fetchone()[0]
    print(f"Customer_Profile total distinct Customer_Id: {total_prof}")

    # Check matches in Deposit_Monthly_Activity and Loan_Contract_Info
    q_v11 = """
    WITH Prof AS (
        SELECT DISTINCT Customer_Id AS cid FROM dbo.Customer_Profile
    ),
    MatchedDeposit AS (
        SELECT DISTINCT p.cid
        FROM Prof p
        JOIN dbo.Deposit_Monthly_Activity d ON d.customer_id = p.cid
    ),
    MatchedLoan AS (
        SELECT DISTINCT p.cid
        FROM Prof p
        JOIN dbo.Loan_Contract_Info l ON l.MAIN_CUSTOMER_ID = p.cid
    )
    SELECT 
        (SELECT COUNT(*) FROM MatchedDeposit) AS in_deposit,
        (SELECT COUNT(*) FROM MatchedLoan) AS in_loan,
        (SELECT COUNT(*) FROM (SELECT cid FROM MatchedDeposit UNION SELECT cid FROM MatchedLoan) u) AS in_either
    """
    df_v11 = pd.read_sql(sqlalchemy.text(q_v11), conn)

print("V11 results:")
print(df_v11)
df_v11["total_customer_profile"] = total_prof
df_v11.to_csv("reports/review_S1_S4/results/v11_customer_profile_matches.csv", index=False)
print(f"Done V10 and V11 in {time.time()-t0:.1f}s")
