"""
Time-horizon / continuity check across Customer_Monthly_Activity, Deposit_Monthly_Activity,
and Loan_Monthly_Activity (Persian calendar YYYYMM sequence).
Output: results/time_horizon_stats.txt
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from db_config import get_engine


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
REPORT_PATH = os.path.join(RESULTS_DIR, "time_horizon_stats.txt")


def get_year_mount_distinct(engine, table_name: str) -> pd.DataFrame:
    query = f"""
        SELECT CAST(year_mount AS INT) AS year_month, COUNT(*) AS cnt
        FROM {table_name}
        WHERE year_mount IS NOT NULL
        GROUP BY CAST(year_mount AS INT)
        ORDER BY year_month
    """
    return pd.read_sql(query, engine)


def get_loan_payed_date_year_month(engine) -> pd.DataFrame:
    query = """
        WITH cleaned AS (
            SELECT REPLACE(payed_date, CHAR(34), '') AS pd_clean
            FROM Loan_Monthly_Activity
            WHERE payed_date IS NOT NULL AND LTRIM(RTRIM(REPLACE(payed_date, CHAR(34), ''))) <> ''
        )
        SELECT
            CAST(SUBSTRING(pd_clean, 1, 4) AS INT) * 100 + CAST(SUBSTRING(pd_clean, 6, 2) AS INT) AS year_month,
            COUNT(*) AS cnt
        FROM cleaned
        GROUP BY CAST(SUBSTRING(pd_clean, 1, 4) AS INT) * 100 + CAST(SUBSTRING(pd_clean, 6, 2) AS INT)
        ORDER BY year_month
    """
    return pd.read_sql(query, engine)


def build_ideal_sequence(min_ym: int, max_ym: int) -> list:
    min_year, min_month = divmod(min_ym, 100)
    max_year, max_month = divmod(max_ym, 100)
    sequence = []
    year, month = min_year, min_month
    while (year, month) <= (max_year, max_month):
        sequence.append(year * 100 + month)
        month += 1
        if month > 12:
            month = 1
            year += 1
    return sequence


def find_missing(distinct_values: list, min_ym: int, max_ym: int) -> list:
    ideal = build_ideal_sequence(min_ym, max_ym)
    actual_set = set(distinct_values)
    return [ym for ym in ideal if ym not in actual_set]


def format_ym(ym: int) -> str:
    year, month = divmod(ym, 100)
    return f"{year:04d}/{month:02d}"


def report_section(lines: list, table_label: str, df: pd.DataFrame):
    lines.append(f"TABLE: {table_label}")
    lines.append("-" * 70)
    if df.empty:
        lines.append("No distinct year_month values found.")
        lines.append("")
        return

    distinct_values = df["year_month"].tolist()
    min_ym = int(df["year_month"].min())
    max_ym = int(df["year_month"].max())
    total_distinct = len(distinct_values)
    ideal_length = len(build_ideal_sequence(min_ym, max_ym))
    missing = find_missing(distinct_values, min_ym, max_ym)

    lines.append(f"MIN year_month: {min_ym} ({format_ym(min_ym)})")
    lines.append(f"MAX year_month: {max_ym} ({format_ym(max_ym)})")
    lines.append(f"Total distinct months (actual): {total_distinct}")
    lines.append(f"Expected months in ideal continuous sequence (MIN..MAX): {ideal_length}")
    lines.append(f"Missing months count: {len(missing)}")
    if missing:
        lines.append("Missing months list:")
        for ym in missing:
            lines.append(f"  {ym} ({format_ym(ym)})")
    lines.append("")
    lines.append("Full distinct month list with record counts:")
    for _, row in df.iterrows():
        lines.append(f"  {int(row['year_month'])} ({format_ym(int(row['year_month']))}): {row['cnt']} records")
    lines.append("")


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    engine = get_engine()

    lines = []
    lines.append("Time Horizon & Continuity Check (Persian Calendar YYYYMM)")
    lines.append("=" * 70)
    lines.append(f"Generated at: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    cma_df = get_year_mount_distinct(engine, "Customer_Monthly_Activity")
    report_section(lines, "Customer_Monthly_Activity (year_mount)", cma_df)

    dma_df = get_year_mount_distinct(engine, "Deposit_Monthly_Activity")
    report_section(lines, "Deposit_Monthly_Activity (year_mount)", dma_df)

    loan_df = get_loan_payed_date_year_month(engine)
    report_section(lines, "Loan_Monthly_Activity (derived from payed_date)", loan_df)

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Saved: {REPORT_PATH}")


if __name__ == "__main__":
    main()
