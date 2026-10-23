"""
USED_COST vs APPROVED_AMOUNT ratio extraction - Loan_Contract_Info.
Output: results/used_cost_stats.txt
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from db_config import get_engine

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
REPORT_PATH = os.path.join(RESULTS_DIR, "used_cost_stats.txt")

PERCENTILES = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]


def fetch_loan_data(engine) -> pd.DataFrame:
    query = """
        SELECT LOANFILE_ID, MAIN_CUSTOMER_ID, USED_COST, APPROVED_AMOUNT
        FROM Loan_Contract_Info
    """
    return pd.read_sql(query, engine)


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    engine = get_engine()

    df = fetch_loan_data(engine)
    total_rows = len(df)

    df["APPROVED_AMOUNT"] = pd.to_numeric(df["APPROVED_AMOUNT"], errors="coerce")
    df["USED_COST"] = pd.to_numeric(df["USED_COST"], errors="coerce")

    null_approved = int(df["APPROVED_AMOUNT"].isna().sum())
    zero_approved = int((df["APPROVED_AMOUNT"] == 0).sum())

    filtered = df[df["APPROVED_AMOUNT"].notna() & (df["APPROVED_AMOUNT"] != 0)].copy()
    filtered_rows = len(filtered)

    filtered["Collateral_Coverage_Ratio"] = (
        filtered["USED_COST"] / filtered["APPROVED_AMOUNT"]
    )

    ratio = filtered["Collateral_Coverage_Ratio"]
    null_used_cost = int(filtered["USED_COST"].isna().sum())

    ratio_valid = ratio.dropna()

    desc_min = ratio_valid.min()
    desc_max = ratio_valid.max()
    desc_mean = ratio_valid.mean()
    desc_median = ratio_valid.median()

    percentile_values = ratio_valid.quantile(PERCENTILES)

    cnt_eq_zero = int((ratio_valid == 0).sum())
    cnt_lt_one = int((ratio_valid < 1.0).sum())
    cnt_ge_one = int((ratio_valid >= 1.0).sum())

    lines = []
    lines.append("USED_COST / APPROVED_AMOUNT Ratio - Raw Statistical Extraction")
    lines.append("Table: Loan_Contract_Info")
    lines.append("=" * 70)
    lines.append(f"Generated at: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    lines.append("RECORD COUNTS")
    lines.append("-" * 70)
    lines.append(f"Total records (Loan_Contract_Info): {total_rows}")
    lines.append(f"NULL APPROVED_AMOUNT: {null_approved}")
    lines.append(f"Zero APPROVED_AMOUNT: {zero_approved}")
    lines.append(f"Records after filtering (APPROVED_AMOUNT not null and not zero): {filtered_rows}")
    lines.append(f"NULL USED_COST within filtered records: {null_used_cost}")
    lines.append(f"Valid ratio records: {len(ratio_valid)}")
    lines.append("")

    lines.append("DESCRIPTIVE STATISTICS (Collateral_Coverage_Ratio)")
    lines.append("-" * 70)
    lines.append(f"Min: {desc_min}")
    lines.append(f"Max: {desc_max}")
    lines.append(f"Mean: {desc_mean}")
    lines.append(f"Median: {desc_median}")
    lines.append("")

    lines.append("PERCENTILES (Collateral_Coverage_Ratio)")
    lines.append("-" * 70)
    for p in PERCENTILES:
        lines.append(f"P{p*100:g}: {percentile_values[p]}")
    lines.append("")

    lines.append("RATIO DISTRIBUTION COUNTS")
    lines.append("-" * 70)
    lines.append(f"Ratio == 0: {cnt_eq_zero}")
    lines.append(f"Ratio < 1.0: {cnt_lt_one}")
    lines.append(f"Ratio >= 1.0: {cnt_ge_one}")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Saved: {REPORT_PATH}")


if __name__ == "__main__":
    main()
