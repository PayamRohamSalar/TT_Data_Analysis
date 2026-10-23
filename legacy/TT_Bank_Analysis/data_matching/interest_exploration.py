"""
Interest-paid-to-depositors exploration.
Task 1: Customer_Monthly_Activity - transactions with 'سود' in title.
Task 2: Deposit tables - keyword search for Balance / Interest Rate columns.
Output: results/interest_exploration_stats.txt
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from db_config import get_engine

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
REPORT_PATH = os.path.join(RESULTS_DIR, "interest_exploration_stats.txt")

DEPOSIT_TABLES = ["Deposit_Monthly_Activity", "Deposit_Accoutnt_Info", "Deposit_Customer"]

BALANCE_KEYWORDS = ["%balance%", "%mande%", "%amount%"]
RATE_KEYWORDS = ["%rate%", "%nerkh%", "%profit%", "%sood%"]


def task1_sood_titles(engine) -> pd.DataFrame:
    query = """
        SELECT code, title, COUNT(*) AS record_count, SUM(amount_eq) AS total_amount_eq
        FROM Customer_Monthly_Activity
        WHERE title LIKE N'%سود%'
        GROUP BY code, title
        ORDER BY record_count DESC
    """
    return pd.read_sql(query, engine)


def get_table_columns(engine, table_name: str) -> pd.DataFrame:
    query = f"""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = '{table_name}'
    """
    return pd.read_sql(query, engine)


def filter_keyword_columns(columns_df: pd.DataFrame, keywords: list) -> list:
    matches = []
    for col in columns_df["COLUMN_NAME"]:
        col_lower = col.lower()
        for kw in keywords:
            kw_clean = kw.strip("%")
            if kw_clean in col_lower:
                matches.append(col)
                break
    return matches


def sample_columns(engine, table_name: str, columns: list, n: int = 5) -> pd.DataFrame:
    if not columns:
        return pd.DataFrame()
    col_list = ", ".join(columns)
    query = f"SELECT TOP {n} {col_list} FROM {table_name}"
    return pd.read_sql(query, engine)


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    engine = get_engine()

    lines = []
    lines.append("Interest-Paid-to-Depositors Exploration")
    lines.append("=" * 70)
    lines.append(f"Generated at: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Task 1
    lines.append("TASK 1: Customer_Monthly_Activity - title LIKE N'%سود%'")
    lines.append("-" * 70)
    sood_df = task1_sood_titles(engine)
    lines.append(f"Distinct (code, title) combinations found: {len(sood_df)}")
    lines.append("")
    lines.append(f"{'code':>10} {'record_count':>14} {'total_amount_eq':>20}  title")
    for _, row in sood_df.iterrows():
        lines.append(
            f"{row['code']!s:>10} {row['record_count']:>14} {row['total_amount_eq']:>20}  {row['title']}"
        )
    lines.append("")

    # Task 2
    lines.append("TASK 2: Deposit tables - Balance / Interest Rate column search")
    lines.append("-" * 70)
    for table in DEPOSIT_TABLES:
        cols_df = get_table_columns(engine, table)
        lines.append(f"Table: {table} ({len(cols_df)} columns)")
        for _, row in cols_df.iterrows():
            lines.append(f"    {row['COLUMN_NAME']} ({row['DATA_TYPE']})")

        balance_matches = filter_keyword_columns(cols_df, BALANCE_KEYWORDS)
        rate_matches = filter_keyword_columns(cols_df, RATE_KEYWORDS)

        lines.append(f"  Balance-keyword matches: {balance_matches if balance_matches else 'NONE'}")
        lines.append(f"  Rate-keyword matches: {rate_matches if rate_matches else 'NONE'}")

        combined_matches = list(dict.fromkeys(balance_matches + rate_matches))
        if combined_matches:
            sample_df = sample_columns(engine, table, combined_matches)
            lines.append(f"  Sample (TOP 5) of matched columns:")
            lines.append("  " + sample_df.to_string(index=False).replace("\n", "\n  "))
        lines.append("")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Saved: {REPORT_PATH}")


if __name__ == "__main__":
    main()
