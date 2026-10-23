import time
import pandas as pd
import sqlalchemy
from tt_bank.db.connection import get_engine

t0 = time.time()
engine = get_engine()
print("Running Special Question 2: Ground Truth Test for Inferred Borrower Rule...")

with engine.connect() as conn:
    # 1. For contracts in 140412 that HAVE a contract record:
    # Check single-party contracts: is the single party in Loan_Remain equal to main_customer_id?
    q_gt = """
    WITH BaseRemain AS (
        SELECT loanfile_id, customer_id, MAX(Total_Remain) AS tot
        FROM dbo.Loan_Remain 
        WHERE Transaction_Date BETWEEN 14041201 AND 14041231
        GROUP BY loanfile_id, customer_id
    ),
    ContractSummary AS (
        SELECT loanfile_id, COUNT(*) AS n_parties, MAX(tot) AS contract_tot
        FROM BaseRemain
        GROUP BY loanfile_id
    )
    SELECT 
        cs.loanfile_id,
        cs.n_parties,
        cs.contract_tot,
        br.customer_id AS party_customer_id,
        c.main_customer_id,
        CASE WHEN br.customer_id = c.main_customer_id THEN 1 ELSE 0 END AS is_main
    FROM ContractSummary cs
    JOIN dbo.vw_Loan_Contract_Dedup c ON c.loanfile_id = cs.loanfile_id
    JOIN BaseRemain br ON br.loanfile_id = cs.loanfile_id
    WHERE cs.contract_tot > 0
    """
    df = pd.read_sql(sqlalchemy.text(q_gt), conn)

print(f"Loaded {len(df):,} contract-party rows in {time.time()-t0:.1f}s")

# Analyze single-party contracts (n_parties == 1)
single_p = df[df["n_parties"] == 1]
n_single_contracts = single_p["loanfile_id"].nunique()
matches = (single_p["party_customer_id"] == single_p["main_customer_id"]).sum()
mismatches = n_single_contracts - matches
accuracy = (matches / n_single_contracts) * 100

print(f"\n--- Ground Truth on Single-Party Contracts with Record (140412) ---")
print(f"Total single-party contracts with record: {n_single_contracts:,}")
print(f"Matches (single party == main_customer_id): {matches:,} ({accuracy:.4f}%)")
print(f"Mismatches (single party != main_customer_id): {mismatches:,} ({100-accuracy:.4f}%)")

# What about multi-party contracts (n_parties > 1)?
multi_p = df[df["n_parties"] > 1]
n_multi_contracts = multi_p["loanfile_id"].nunique()
main_in_parties = multi_p.groupby("loanfile_id")["is_main"].max()
main_present_count = main_in_parties.sum()
main_missing_count = n_multi_contracts - main_present_count
pct_main_present = (main_present_count / n_multi_contracts) * 100

print(f"\n--- Multi-Party Contracts with Record (140412) ---")
print(f"Total multi-party contracts with record: {n_multi_contracts:,}")
print(f"Contracts where main_customer_id is among parties: {main_present_count:,} ({pct_main_present:.2f}%)")
print(f"Contracts where main_customer_id is NOT among parties: {main_missing_count:,} ({100-pct_main_present:.2f}%)")

# Party distribution of multi-party contracts
party_counts = df.groupby("loanfile_id")["n_parties"].first().value_counts().sort_index()
print("\nDistribution of parties per contract:")
print(party_counts.head(10))

res_sq2 = pd.DataFrame([{
    "test": "Single-party contracts with record: party == main_customer_id",
    "total_contracts": n_single_contracts,
    "matches": matches,
    "mismatches": mismatches,
    "accuracy_pct": accuracy
}, {
    "test": "Multi-party contracts with record: main_customer_id in parties",
    "total_contracts": n_multi_contracts,
    "matches": main_present_count,
    "mismatches": main_missing_count,
    "accuracy_pct": pct_main_present
}])
res_sq2.to_csv("reports/review_S1_S4/results/sq02_inferred_ground_truth.csv", index=False)
print("Saved to sq02_inferred_ground_truth.csv")
