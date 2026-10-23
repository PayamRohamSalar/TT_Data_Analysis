"""
LOAN_PREFERED_RATE frequency distribution extraction - Loan_Contract_Info.
Output: results/loan_prefered_rate_stats.txt
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from db_config import get_engine

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
REPORT_PATH = os.path.join(RESULTS_DIR, "loan_prefered_rate_stats.txt")


def fetch_rate_column(engine) -> pd.DataFrame:
    query = "SELECT LOAN_PREFERED_RATE FROM Loan_Contract_Info"
    return pd.read_sql(query, engine)


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    engine = get_engine()

    df = fetch_rate_column(engine)
    total_rows = len(df)

    raw = df["LOAN_PREFERED_RATE"]
    null_mask = raw.isna()
    blank_mask = raw.astype(str).str.strip().eq("") & ~null_mask
    numeric_series = pd.to_numeric(raw, errors="coerce")
    non_numeric_mask = numeric_series.isna() & ~null_mask & ~blank_mask

    null_count = int(null_mask.sum())
    blank_count = int(blank_mask.sum())
    non_numeric_count = int(non_numeric_mask.sum())

    valid = numeric_series.dropna()

    cnt_negative = int((valid < 0).sum())
    cnt_zero = int((valid == 0).sum())
    cnt_positive = int((valid > 0).sum())

    freq_table = valid.value_counts().sort_index()

    lines = []
    lines.append("LOAN_PREFERED_RATE - Frequency Distribution Extraction")
    lines.append("Table: Loan_Contract_Info")
    lines.append("=" * 70)
    lines.append(f"Generated at: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    lines.append("RECORD COUNTS")
    lines.append("-" * 70)
    lines.append(f"Total records (Loan_Contract_Info): {total_rows}")
    lines.append(f"Null records: {null_count}")
    lines.append(f"Blank records: {blank_count}")
    lines.append(f"Non-numeric records: {non_numeric_count}")
    lines.append(f"Valid numeric records: {len(valid)}")
    lines.append("")

    lines.append("CATEGORICAL BREAKDOWN")
    lines.append("-" * 70)
    lines.append(f"LOAN_PREFERED_RATE < 0 (Negative): {cnt_negative}")
    lines.append(f"LOAN_PREFERED_RATE == 0 (Zero): {cnt_zero}")
    lines.append(f"LOAN_PREFERED_RATE > 0 (Positive): {cnt_positive}")
    lines.append("")

    lines.append("FULL FREQUENCY DISTRIBUTION (sorted ascending by value)")
    lines.append("-" * 70)
    lines.append(f"{'LOAN_PREFERED_RATE':>20} {'count':>12}")
    for value, count in freq_table.items():
        lines.append(f"{value:>20} {count:>12}")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Saved: {REPORT_PATH}")


if __name__ == "__main__":
    main()
