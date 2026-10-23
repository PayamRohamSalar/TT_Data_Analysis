"""
Date/Status data-quality deep dive on Loan_Monthly_Activity, in preparation for
reconstructing a Monthly Snapshot (Balance/DPD) from installment-level rows.
Output: results/loan_snapshot_prep_stats.txt
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from db_config import get_engine

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
REPORT_PATH = os.path.join(RESULTS_DIR, "loan_snapshot_prep_stats.txt")

TABLE = "Loan_Monthly_Activity"
SUSPICIOUS_YEARS = ["1300", "1301", "1390", "1900"]


def get_status_distribution(engine) -> pd.DataFrame:
    query = f"""
        SELECT Status, COUNT(*) AS cnt
        FROM {TABLE}
        GROUP BY Status
        ORDER BY cnt DESC
    """
    return pd.read_sql(query, engine)


def get_date_quality(engine, column: str) -> dict:
    suspicious_conditions = " OR ".join(
        f"{column} LIKE '%{yr}%'" for yr in SUSPICIOUS_YEARS
    )
    query = f"""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN {column} IS NULL THEN 1 ELSE 0 END) AS null_cnt,
            SUM(CASE WHEN LTRIM(RTRIM(REPLACE({column}, CHAR(34), ''))) = '' THEN 1 ELSE 0 END) AS blank_cnt,
            SUM(CASE WHEN {suspicious_conditions} THEN 1 ELSE 0 END) AS suspicious_cnt
        FROM {TABLE}
    """
    return pd.read_sql(query, engine).iloc[0].to_dict()


def get_sample_loanfile_id(engine, min_rows: int = 15, max_rows: int = 30):
    query = f"""
        SELECT TOP 1 loanfile_id, COUNT(*) AS cnt
        FROM {TABLE}
        GROUP BY loanfile_id
        HAVING COUNT(*) BETWEEN {min_rows} AND {max_rows}
    """
    df = pd.read_sql(query, engine)
    if df.empty:
        query_fallback = f"""
            SELECT TOP 1 loanfile_id, COUNT(*) AS cnt
            FROM {TABLE}
            GROUP BY loanfile_id
            HAVING COUNT(*) >= {min_rows}
        """
        df = pd.read_sql(query_fallback, engine)
    if df.empty:
        return None, 0
    return int(df["loanfile_id"].iloc[0]), int(df["cnt"].iloc[0])


def get_loanfile_sequence(engine, loanfile_id: int) -> pd.DataFrame:
    query = f"""
        SELECT loanfile_id, delivery_date, payed_date, Status,
               installment_main, installment_interest, installment_penalty
        FROM {TABLE}
        WHERE loanfile_id = {loanfile_id}
        ORDER BY delivery_date
    """
    return pd.read_sql(query, engine)


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    engine = get_engine()

    lines = []
    lines.append(f"{TABLE} - Date/Status Data Quality Deep Dive")
    lines.append("=" * 70)
    lines.append(f"Generated at: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    lines.append("1) Status COLUMN DISTRIBUTION")
    lines.append("-" * 70)
    status_df = get_status_distribution(engine)
    for _, row in status_df.iterrows():
        lines.append(f"  {row['Status']}: {row['cnt']}")
    lines.append("")

    lines.append("2) payed_date DATA QUALITY")
    lines.append("-" * 70)
    payed_q = get_date_quality(engine, "payed_date")
    lines.append(f"  Total records: {payed_q['total']}")
    lines.append(f"  NULL: {payed_q['null_cnt']}")
    lines.append(f"  Blank/empty (after stripping quotes/spaces): {payed_q['blank_cnt']}")
    lines.append(f"  Suspicious years {SUSPICIOUS_YEARS}: {payed_q['suspicious_cnt']}")
    lines.append("")

    lines.append("3) delivery_date DATA QUALITY")
    lines.append("-" * 70)
    delivery_q = get_date_quality(engine, "delivery_date")
    lines.append(f"  Total records: {delivery_q['total']}")
    lines.append(f"  NULL: {delivery_q['null_cnt']}")
    lines.append(f"  Blank/empty (after stripping quotes/spaces): {delivery_q['blank_cnt']}")
    lines.append(f"  Suspicious years {SUSPICIOUS_YEARS}: {delivery_q['suspicious_cnt']}")
    lines.append("")

    lines.append("4) SINGLE-CONTRACT INSTALLMENT SEQUENCE SAMPLE")
    lines.append("-" * 70)
    loanfile_id, row_count = get_sample_loanfile_id(engine)
    if loanfile_id is None:
        lines.append("  No loanfile_id with >= 15 rows was found.")
    else:
        lines.append(f"  Selected loanfile_id: {loanfile_id} (total rows in table: {row_count})")
        lines.append("")
        seq_df = get_loanfile_sequence(engine, loanfile_id)
        lines.append(seq_df.to_string(index=False))

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Saved: {REPORT_PATH}")


if __name__ == "__main__":
    main()
