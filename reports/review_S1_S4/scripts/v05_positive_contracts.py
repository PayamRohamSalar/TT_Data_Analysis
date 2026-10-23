import pandas as pd
import sqlalchemy
from tt_bank.db.connection import get_engine

engine = get_engine()
with engine.connect() as conn:
    q = """
    WITH BaseRemain AS (
        SELECT loanfile_id, customer_id, MAX(Total_Remain) AS tot
        FROM dbo.Loan_Remain 
        WHERE Transaction_Date BETWEEN 14041201 AND 14041231
        GROUP BY loanfile_id, customer_id
    ),
    ContractSummary AS (
        SELECT loanfile_id, MAX(tot) AS contract_tot, COUNT(*) AS n_parties
        FROM BaseRemain
        GROUP BY loanfile_id
    )
    SELECT 
        COUNT(*) AS total_contracts_with_pos_bal,
        SUM(CASE WHEN c.loanfile_id IS NULL THEN 1 ELSE 0 END) AS no_rec_contracts,
        SUM(CASE WHEN c.loanfile_id IS NULL AND cs.n_parties = 1 THEN 1 ELSE 0 END) AS single_party_no_rec,
        SUM(CASE WHEN c.loanfile_id IS NULL THEN cs.contract_tot ELSE 0 END) AS no_rec_bal,
        SUM(CASE WHEN c.loanfile_id IS NULL AND cs.n_parties = 1 THEN cs.contract_tot ELSE 0 END) AS single_party_no_rec_bal
    FROM ContractSummary cs
    LEFT JOIN dbo.vw_Loan_Contract_Dedup c ON c.loanfile_id = cs.loanfile_id
    WHERE cs.contract_tot > 0
    """
    df = pd.read_sql(sqlalchemy.text(q), conn)

print("Contracts with positive balance (contract_tot > 0):")
print(df)

no_rec = df.loc[0, "no_rec_contracts"]
sp = df.loc[0, "single_party_no_rec"]
no_rec_bal = df.loc[0, "no_rec_bal"]
sp_bal = df.loc[0, "single_party_no_rec_bal"]
share = (sp_bal / no_rec_bal) * 100

print(f"no_rec_contracts: {no_rec} (Claimed: 128,639)")
print(f"single_party_no_rec: {sp} (Claimed: 108,674)")
print(f"share: {share:.2f}% (Claimed: 88.9%)")
print(f"no_rec_bal (Hemmat): {no_rec_bal / 1e13:.2f}")
print(f"sp_bal (Hemmat): {sp_bal / 1e13:.2f}")

df_out = pd.DataFrame([{
    "metric": "V5 Contracts > 0 without record",
    "claimed": "128,639",
    "calculated": str(no_rec),
    "diff": no_rec - 128639
}, {
    "metric": "V5 Single-party contracts > 0 without record",
    "claimed": "108,674",
    "calculated": str(sp),
    "diff": sp - 108674
}, {
    "metric": "V5 Balance share of single-party",
    "claimed": "88.9%",
    "calculated": f"{share:.2f}%",
    "diff": f"{share - 88.9:.2f}%"
}, {
    "metric": "V5 Balance without record (Hemmat)",
    "claimed": "28.7 (contractual) / 33.35 (party)",
    "calculated": f"{no_rec_bal / 1e13:.2f}",
    "diff": ""
}, {
    "metric": "V5 Balance single-party (Hemmat)",
    "claimed": "25.52",
    "calculated": f"{sp_bal / 1e13:.2f}",
    "diff": ""
}])
df_out.to_csv("reports/review_S1_S4/results/v5_positive_balance_check.csv", index=False)
