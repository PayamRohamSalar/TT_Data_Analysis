"""
Fee-code verification and aggregation-potential check - Customer_Monthly_Activity.
Output: results/fee_structure_summary.txt
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from db_config import get_engine

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
REPORT_PATH = os.path.join(RESULTS_DIR, "fee_structure_summary.txt")

TABLE = "Customer_Monthly_Activity"
FEE_KEYWORDS = ["کارمزد", "کارمزدها", "حق الزحمه"]


def get_matched_fee_codes(engine) -> pd.DataFrame:
    conditions = " OR ".join(f"title LIKE N'%{kw}%'" for kw in FEE_KEYWORDS)
    query = f"""
        SELECT code, title, COUNT(*) AS record_count,
               SUM(amount_eq) AS total_amount_eq
        FROM {TABLE}
        WHERE {conditions}
        GROUP BY code, title
        ORDER BY record_count DESC
    """
    return pd.read_sql(query, engine)


def get_overall_totals(engine) -> pd.Series:
    conditions = " OR ".join(f"title LIKE N'%{kw}%'" for kw in FEE_KEYWORDS)
    query = f"""
        SELECT
            COUNT(*) AS total_fee_records,
            SUM(amount_eq) AS total_fee_amount_eq,
            COUNT(DISTINCT main_customer_id) AS distinct_customers
        FROM {TABLE}
        WHERE {conditions}
    """
    return pd.read_sql(query, engine).iloc[0]


def get_multi_code_month_count(engine, year_mount_filter=None) -> int:
    conditions = " OR ".join(f"title LIKE N'%{kw}%'" for kw in FEE_KEYWORDS)
    scope = f"AND year_mount = {year_mount_filter}" if year_mount_filter is not None else ""
    query = f"""
        SELECT COUNT(*) AS cnt FROM (
            SELECT main_customer_id, year_mount
            FROM {TABLE}
            WHERE ({conditions}) {scope}
            GROUP BY main_customer_id, year_mount
            HAVING COUNT(DISTINCT code) > 1
        ) t
    """
    return int(pd.read_sql(query, engine)["cnt"].iloc[0])


def get_max_year_mount(engine):
    query = f"SELECT MAX(year_mount) AS max_ym FROM {TABLE}"
    return pd.read_sql(query, engine)["max_ym"].iloc[0]


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    engine = get_engine()

    lines = []
    lines.append(f"{TABLE} - Fee Code Verification & Aggregation Check")
    lines.append("=" * 70)
    lines.append(f"Generated at: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Fee keywords used: {FEE_KEYWORDS}")
    lines.append("")

    lines.append("1) MATCHED FEE CODES/TITLES")
    lines.append("-" * 70)
    matched_df = get_matched_fee_codes(engine)
    lines.append(f"Distinct (code, title) fee combinations found: {len(matched_df)}")
    lines.append("")
    lines.append(f"{'code':>10} {'record_count':>14} {'total_amount_eq':>20}  title")
    for _, row in matched_df.iterrows():
        lines.append(
            f"{row['code']!s:>10} {row['record_count']:>14} {row['total_amount_eq']:>20}  {row['title']}"
        )
    lines.append("")

    lines.append("2) OVERALL TOTALS (all matched fee records)")
    lines.append("-" * 70)
    totals = get_overall_totals(engine)
    lines.append(f"Total fee records: {totals['total_fee_records']}")
    lines.append(f"Total fee amount_eq (sum): {totals['total_fee_amount_eq']}")
    lines.append(f"Distinct customers with fee records: {totals['distinct_customers']}")
    lines.append("")

    lines.append("3) MULTI-CODE PER CUSTOMER-MONTH CHECK")
    lines.append("-" * 70)
    try:
        multi_count = get_multi_code_month_count(engine)
        lines.append(
            f"Customer-month combinations with more than one distinct fee code (full table): {multi_count}"
        )
    except Exception as e:
        lines.append("FULL-TABLE QUERY FAILED - could not complete due to a database error.")
        lines.append(f"Error detail: {str(e).splitlines()[0]}")
        lines.append("")
        lines.append("Retrying with scope reduced to a single year_mount (most recent month)...")
        try:
            max_ym = get_max_year_mount(engine)
            multi_count = get_multi_code_month_count(engine, year_mount_filter=max_ym)
            lines.append(f"Scope: year_mount = {max_ym}")
            lines.append(
                f"Customer-month combinations with more than one distinct fee code (scoped): {multi_count}"
            )
        except Exception as e2:
            lines.append("SCOPED QUERY ALSO FAILED.")
            lines.append(f"Error detail: {str(e2).splitlines()[0]}")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Saved: {REPORT_PATH}")


if __name__ == "__main__":
    main()
