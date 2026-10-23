import time
import pandas as pd
import sqlalchemy
from tt_bank.db.connection import get_engine

t0 = time.time()
engine = get_engine()

print("Connecting to DB for Loan analysis (V3, V4, V5, V6)...")
with engine.connect() as conn:
    # V6: Check if any LOANFILE_ID has more than 1 distinct MAIN_CUSTOMER_ID
    print("Checking V6: distinct MAIN_CUSTOMER_ID per LOANFILE_ID in Loan_Contract_Info...")
    q_v6 = """
    SELECT COUNT(*) AS multi_main_cust_count
    FROM (
        SELECT LOANFILE_ID
        FROM dbo.Loan_Contract_Info
        GROUP BY LOANFILE_ID
        HAVING COUNT(DISTINCT MAIN_CUSTOMER_ID) > 1
    ) t
    """
    v6_res = conn.execute(sqlalchemy.text(q_v6)).fetchone()[0]
    print(f"V6 result: {v6_res} (Claimed: 0)")

    # V3, V4, V5: Loan_Remain 140412 analysis
    # Let's inspect the contracts in 140412:
    print("Querying 140412 Loan_Remain aggregated by contract...")
    q_contracts = """
    WITH BaseRemain AS (
        SELECT loanfile_id, customer_id, 
               MAX(Total_Remain) AS tot,
               MAX(MANDE_JARI) AS jari
        FROM dbo.Loan_Remain 
        WHERE Transaction_Date BETWEEN 14041201 AND 14041231
        GROUP BY loanfile_id, customer_id
    ),
    ContractSummary AS (
        SELECT loanfile_id,
               MAX(tot) AS contract_tot,
               COUNT(*) AS n_parties
        FROM BaseRemain
        GROUP BY loanfile_id
    )
    SELECT 
        cs.loanfile_id,
        cs.contract_tot,
        cs.n_parties,
        c.main_customer_id,
        CASE WHEN c.loanfile_id IS NOT NULL THEN 1 ELSE 0 END AS has_contract_record
    FROM ContractSummary cs
    LEFT JOIN dbo.vw_Loan_Contract_Dedup c ON c.loanfile_id = cs.loanfile_id
    """
    # Note: If this takes a couple of minutes, we can run it and wait
    df_contracts = pd.read_sql(sqlalchemy.text(q_contracts), conn)

print(f"Loaded {len(df_contracts)} contracts in {time.time()-t0:.1f}s")

# V3: Total loan balance in 12/1404 after deduplication (contract, month)
total_loan_bal = df_contracts["contract_tot"].sum()
total_loan_hemmat = total_loan_bal / 1e13
print(f"V3: Total loan balance: {total_loan_bal:,.0f} Rials = {total_loan_hemmat:.2f} Hemmat (Claimed: 128.2 Hemmat)")

# V5: Contracts with balance in 12/1404 without contract record and single-party contracts
no_contract_rec = df_contracts[df_contracts["has_contract_record"] == 0]
n_no_contract = len(no_contract_rec)
bal_no_contract = no_contract_rec["contract_tot"].sum()

single_party = no_contract_rec[no_contract_rec["n_parties"] == 1]
n_single_party = len(single_party)
bal_single_party = single_party["contract_tot"].sum()
share_single_party_bal = (bal_single_party / bal_no_contract) * 100 if bal_no_contract > 0 else 0

print(f"V5: Contracts without record: {n_no_contract:,} (Claimed: 128,639)")
print(f"V5: Single-party contracts: {n_single_party:,} (Claimed: 108,674)")
print(f"V5: Balance share of single-party: {share_single_party_bal:.2f}% (Claimed: 88.9%)")

# V4: Count of contractual main borrowers with positive balance, and inferred borrowers
# Contractual borrowers: distinct main_customer_id for contracts with record having positive balance
contractual_borrowers = df_contracts[
    (df_contracts["has_contract_record"] == 1) & (df_contracts["contract_tot"] > 0)
]["main_customer_id"].dropna().unique()
n_contractual_borrowers = len(contractual_borrowers)

# For inferred borrowers, we need the customer_id of single-party contracts without contract record.
# Let's get customer_id for inferred from BaseRemain query or check customer_month_loan_v2
print("Getting customer IDs for single-party contracts without record...")
with engine.connect() as conn:
    q_inferred = """
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
    SELECT DISTINCT br.customer_id
    FROM BaseRemain br
    JOIN ContractSummary cs ON cs.loanfile_id = br.loanfile_id
    LEFT JOIN dbo.vw_Loan_Contract_Dedup c ON c.loanfile_id = br.loanfile_id
    WHERE c.loanfile_id IS NULL AND cs.n_parties = 1 AND cs.contract_tot > 0
    """
    df_inferred_cust = pd.read_sql(sqlalchemy.text(q_inferred), conn)

inferred_borrowers = set(df_inferred_cust["customer_id"].dropna().astype("int64"))
n_inferred_borrowers = len(inferred_borrowers)

# Total distinct primary borrowers (contractual + inferred)
contractual_set = set(pd.Series(contractual_borrowers).astype("int64"))
total_primary_borrowers = len(contractual_set.union(inferred_borrowers))
# Also check if any overlap
overlap = len(contractual_set.intersection(inferred_borrowers))

print(f"V4: Contractual main borrowers: {n_contractual_borrowers:,} (Claimed: 355,463)")
print(f"V4: Inferred main borrowers: {n_inferred_borrowers:,} (Claimed: 17,612)")
print(f"V4: Inferred unique only (no overlap with contractual): {len(inferred_borrowers - contractual_set):,}")
print(f"V4: Overlap between contractual and inferred: {overlap:,}")
print(f"V4: Total distinct primary borrowers: {total_primary_borrowers:,} (Claimed: 373,075)")

# Save results
res = pd.DataFrame([{
    "metric": "V3 Total Loan Balance (Hemmat)",
    "claimed": "128.2",
    "calculated": f"{total_loan_hemmat:.2f}",
    "raw_value": total_loan_bal
}, {
    "metric": "V4 Contractual Main Borrowers",
    "claimed": "355,463",
    "calculated": f"{n_contractual_borrowers:,}",
    "raw_value": n_contractual_borrowers
}, {
    "metric": "V4 Inferred Borrowers",
    "claimed": "17,612",
    "calculated": f"{n_inferred_borrowers:,}",
    "raw_value": n_inferred_borrowers
}, {
    "metric": "V4 Total Primary Borrowers (without overlap)",
    "claimed": "373,075",
    "calculated": f"{total_primary_borrowers:,}",
    "raw_value": total_primary_borrowers
}, {
    "metric": "V4 Sum (Contractual + Inferred)",
    "claimed": "373,075",
    "calculated": f"{n_contractual_borrowers + n_inferred_borrowers:,}",
    "raw_value": n_contractual_borrowers + n_inferred_borrowers
}, {
    "metric": "V5 Contracts without Record",
    "claimed": "128,639",
    "calculated": f"{n_no_contract:,}",
    "raw_value": n_no_contract
}, {
    "metric": "V5 Single-party Contracts",
    "claimed": "108,674",
    "calculated": f"{n_single_party:,}",
    "raw_value": n_single_party
}, {
    "metric": "V5 Balance Share Single-Party (%)",
    "claimed": "88.9%",
    "calculated": f"{share_single_party_bal:.2f}%",
    "raw_value": share_single_party_bal
}, {
    "metric": "V6 Multi MAIN_CUSTOMER_ID per LOANFILE_ID",
    "claimed": "0",
    "calculated": str(v6_res),
    "raw_value": v6_res
}])
res.to_csv("reports/review_S1_S4/results/v3_v6_loan_results.csv", index=False)
print("Saved to v3_v6_loan_results.csv")
