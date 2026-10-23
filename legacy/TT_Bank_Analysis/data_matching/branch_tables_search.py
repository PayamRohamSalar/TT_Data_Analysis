"""
Search for branch-level / general-ledger tables across the full database schema.
Output: results/branch_level_exploration.txt
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from db_config import get_engine

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
REPORT_PATH = os.path.join(RESULTS_DIR, "branch_level_exploration.txt")

KEYWORDS = [
    "branch", "shob", "shoab", "gl", "ledger", "profit",
    "interest", "mali", "amalkard", "report", "stat",
]


def get_all_tables(engine) -> pd.DataFrame:
    query = """
        SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
        FROM INFORMATION_SCHEMA.TABLES
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    """
    return pd.read_sql(query, engine)


def filter_by_keywords(tables_df: pd.DataFrame, keywords: list) -> pd.DataFrame:
    pattern = "|".join(keywords)
    mask = tables_df["TABLE_NAME"].str.contains(pattern, case=False, na=False)
    return tables_df[mask]


def sample_table(engine, schema: str, table: str, n: int = 3) -> pd.DataFrame:
    query = f"SELECT TOP {n} * FROM [{schema}].[{table}]"
    return pd.read_sql(query, engine)


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    engine = get_engine()

    all_tables = get_all_tables(engine)
    matched = filter_by_keywords(all_tables, KEYWORDS)

    lines = []
    lines.append("Branch-Level / General Ledger Table Search")
    lines.append("=" * 70)
    lines.append(f"Generated at: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    lines.append(f"Total tables/views in database (all schemas): {len(all_tables)}")
    lines.append("Full table list:")
    for _, row in all_tables.iterrows():
        lines.append(f"  [{row['TABLE_SCHEMA']}].[{row['TABLE_NAME']}] ({row['TABLE_TYPE']})")
    lines.append("")

    lines.append(f"Keywords used: {KEYWORDS}")
    lines.append(f"Matched tables/views: {len(matched)}")
    lines.append("-" * 70)
    if matched.empty:
        lines.append("No table or view names matched the given keywords.")
    else:
        for _, row in matched.iterrows():
            lines.append(f"  [{row['TABLE_SCHEMA']}].[{row['TABLE_NAME']}] ({row['TABLE_TYPE']})")
    lines.append("")

    if not matched.empty:
        lines.append("SAMPLE DATA (TOP 3 rows) FOR TOP 5 MATCHED TABLES")
        lines.append("-" * 70)
        for _, row in matched.head(5).iterrows():
            schema, table = row["TABLE_SCHEMA"], row["TABLE_NAME"]
            lines.append(f"Table: [{schema}].[{table}]")
            try:
                sample_df = sample_table(engine, schema, table)
                lines.append(sample_df.to_string(index=False))
            except Exception as e:
                lines.append(f"  ERROR sampling table: {e}")
            lines.append("")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Saved: {REPORT_PATH}")


if __name__ == "__main__":
    main()
