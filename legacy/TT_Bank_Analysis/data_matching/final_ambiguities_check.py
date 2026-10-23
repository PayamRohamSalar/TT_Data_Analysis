"""
Final data-quality checks before ETL:
Task 1: LOAN_INTEREST_RATE cleanliness (Loan_Contract_Info)
Task 2: Closed-account behavior in Deposit_Monthly_Activity vs Deposit_Accoutnt_Info.CLOSE_DATE
Output: results/final_ambiguities_check.txt
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from db_config import get_engine

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
REPORT_PATH = os.path.join(RESULTS_DIR, "final_ambiguities_check.txt")


# ---------- Task 1 ----------
def get_rate_distribution(engine) -> pd.DataFrame:
    query = """
        SELECT LOAN_INTEREST_RATE, COUNT(*) AS cnt
        FROM Loan_Contract_Info
        GROUP BY LOAN_INTEREST_RATE
        ORDER BY cnt DESC
    """
    return pd.read_sql(query, engine)


def get_rate_null_blank(engine) -> pd.Series:
    query = """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN LOAN_INTEREST_RATE IS NULL THEN 1 ELSE 0 END) AS null_cnt,
            SUM(CASE WHEN LTRIM(RTRIM(LOAN_INTEREST_RATE)) = '' THEN 1 ELSE 0 END) AS blank_cnt
        FROM Loan_Contract_Info
    """
    return pd.read_sql(query, engine).iloc[0]


def get_rate_outliers(engine) -> pd.DataFrame:
    query = """
        SELECT LOAN_INTEREST_RATE, COUNT(*) AS cnt
        FROM Loan_Contract_Info
        WHERE ISNUMERIC(LOAN_INTEREST_RATE) = 1
          AND (CAST(LOAN_INTEREST_RATE AS FLOAT) > 50 OR CAST(LOAN_INTEREST_RATE AS FLOAT) < 0)
        GROUP BY LOAN_INTEREST_RATE
        ORDER BY LOAN_INTEREST_RATE
    """
    return pd.read_sql(query, engine)


def get_rate_non_numeric(engine) -> pd.DataFrame:
    query = """
        SELECT LOAN_INTEREST_RATE, COUNT(*) AS cnt
        FROM Loan_Contract_Info
        WHERE ISNUMERIC(LOAN_INTEREST_RATE) = 0
        GROUP BY LOAN_INTEREST_RATE
        ORDER BY cnt DESC
    """
    return pd.read_sql(query, engine)


# ---------- Task 2 ----------
def get_closed_account_count(engine) -> pd.Series:
    query = """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN CLOSE_DATE IS NULL THEN 1 ELSE 0 END) AS null_close,
            SUM(CASE WHEN LTRIM(RTRIM(CLOSE_DATE)) = '' THEN 1 ELSE 0 END) AS blank_close,
            SUM(CASE WHEN CLOSE_DATE IS NOT NULL AND LTRIM(RTRIM(CLOSE_DATE)) <> '' THEN 1 ELSE 0 END) AS closed_cnt
        FROM Deposit_Accoutnt_Info
    """
    return pd.read_sql(query, engine).iloc[0]


def get_closed_distinct_deposit_id_count(engine) -> int:
    query = """
        SELECT COUNT(DISTINCT DEPOSIT_ID) AS distinct_cnt
        FROM Deposit_Accoutnt_Info
        WHERE CLOSE_DATE IS NOT NULL AND LTRIM(RTRIM(CLOSE_DATE)) <> ''
    """
    return int(pd.read_sql(query, engine)["distinct_cnt"].iloc[0])


def get_sample_closed_deposit_ids(engine, n: int = 5) -> pd.DataFrame:
    query = f"""
        SELECT TOP {n} DEPOSIT_ID, MIN(CLOSE_DATE) AS CLOSE_DATE,
               MIN(OPEN_DATE) AS OPEN_DATE, MIN(STATUS_NAME) AS STATUS_NAME
        FROM Deposit_Accoutnt_Info
        WHERE CLOSE_DATE IS NOT NULL AND LTRIM(RTRIM(CLOSE_DATE)) <> ''
        GROUP BY DEPOSIT_ID
        ORDER BY DEPOSIT_ID
    """
    return pd.read_sql(query, engine)


def get_monthly_activity_for_deposit(engine, deposit_id: str) -> pd.DataFrame:
    query = f"""
        SELECT deposit_id, year_mount, avr_total_amount_eq, sum_creditor_circul_amount_eq
        FROM Deposit_Monthly_Activity
        WHERE deposit_id = {deposit_id}
        ORDER BY year_mount
    """
    return pd.read_sql(query, engine)


def close_date_to_year_mount(close_date: str):
    parts = close_date.strip().split("/")
    if len(parts) >= 2:
        return int(parts[0]) * 100 + int(parts[1])
    return None


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    engine = get_engine()

    lines = []
    lines.append("Final Data Quality Ambiguities Check")
    lines.append("=" * 70)
    lines.append(f"Generated at: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # ---------------- Task 1 ----------------
    lines.append("TASK 1: LOAN_INTEREST_RATE (Loan_Contract_Info)")
    lines.append("-" * 70)
    null_blank = get_rate_null_blank(engine)
    lines.append(f"Total records: {null_blank['total']}")
    lines.append(f"NULL records: {null_blank['null_cnt']}")
    lines.append(f"Blank/space-only records: {null_blank['blank_cnt']}")
    lines.append("")

    non_numeric_df = get_rate_non_numeric(engine)
    lines.append(f"Non-numeric (ISNUMERIC=0) distinct values: {len(non_numeric_df)}")
    for _, row in non_numeric_df.iterrows():
        lines.append(f"  {row['LOAN_INTEREST_RATE']!r}: {row['cnt']}")
    lines.append("")

    outliers_df = get_rate_outliers(engine)
    lines.append(f"Outlier values (numeric, <0 or >50): {len(outliers_df)} distinct value(s)")
    for _, row in outliers_df.iterrows():
        lines.append(f"  {row['LOAN_INTEREST_RATE']}: {row['cnt']}")
    lines.append("")

    dist_df = get_rate_distribution(engine)
    lines.append(f"Full frequency distribution ({len(dist_df)} distinct values):")
    for _, row in dist_df.iterrows():
        lines.append(f"  {row['LOAN_INTEREST_RATE']!s:>10}: {row['cnt']}")
    lines.append("")

    # ---------------- Task 2 ----------------
    lines.append("TASK 2: Closed-Account Behavior (Deposit_Accoutnt_Info / Deposit_Monthly_Activity)")
    lines.append("-" * 70)
    closed_stats = get_closed_account_count(engine)
    lines.append(f"Total Deposit_Accoutnt_Info records: {closed_stats['total']}")
    lines.append(f"NULL CLOSE_DATE: {closed_stats['null_close']}")
    lines.append(f"Blank CLOSE_DATE: {closed_stats['blank_close']}")
    lines.append(f"Closed accounts (CLOSE_DATE populated): {closed_stats['closed_cnt']}")
    distinct_closed_ids = get_closed_distinct_deposit_id_count(engine)
    lines.append(f"Distinct DEPOSIT_ID among closed accounts: {distinct_closed_ids}")
    lines.append("")

    sample_df = get_sample_closed_deposit_ids(engine, n=5)
    lines.append(f"Sampled closed DEPOSIT_IDs ({len(sample_df)}):")
    for _, row in sample_df.iterrows():
        lines.append(
            f"  DEPOSIT_ID={row['DEPOSIT_ID']}  OPEN_DATE={row['OPEN_DATE']}  "
            f"CLOSE_DATE={row['CLOSE_DATE']}  STATUS_NAME={row['STATUS_NAME']}"
        )
    lines.append("")

    for _, row in sample_df.iterrows():
        deposit_id = row["DEPOSIT_ID"]
        close_date = row["CLOSE_DATE"]
        close_ym = close_date_to_year_mount(close_date)
        lines.append(f"--- DEPOSIT_ID {deposit_id} (CLOSE_DATE={close_date}, close_year_month={close_ym}) ---")
        activity_df = get_monthly_activity_for_deposit(engine, deposit_id)
        if activity_df.empty:
            lines.append("  No rows found in Deposit_Monthly_Activity for this deposit_id.")
        else:
            last_ym = int(activity_df["year_mount"].max())
            first_ym = int(activity_df["year_mount"].min())
            row_count = len(activity_df)
            lines.append(
                f"  Rows found: {row_count}, first_year_mount={first_ym}, last_year_mount={last_ym}"
            )
            lines.append(f"  {'year_mount':>12} {'avr_total_amount_eq':>22} {'sum_creditor_circul_amount_eq':>30}")
            for _, arow in activity_df.iterrows():
                lines.append(
                    f"  {int(arow['year_mount']):>12} {arow['avr_total_amount_eq']:>22} "
                    f"{arow['sum_creditor_circul_amount_eq']:>30}"
                )
        lines.append("")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Saved: {REPORT_PATH}")


if __name__ == "__main__":
    main()
