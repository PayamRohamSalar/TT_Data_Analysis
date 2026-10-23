"""
Lightweight schema check - Customer_Monthly_Activity (TOP 5 rows only).
Output: results/monthly_activity_sample.txt
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from db_config import get_engine

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
REPORT_PATH = os.path.join(RESULTS_DIR, "monthly_activity_sample.txt")

TABLE_NAME = "Customer_Monthly_Activity"


def fetch_sample(engine) -> pd.DataFrame:
    query = f"SELECT TOP 5 * FROM {TABLE_NAME}"
    return pd.read_sql(query, engine)


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    engine = get_engine()

    df = fetch_sample(engine)

    lines = []
    lines.append(f"{TABLE_NAME} - Lightweight Schema Check (TOP 5 rows)")
    lines.append("=" * 70)
    lines.append(f"Generated at: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    lines.append(f"COLUMN LIST ({len(df.columns)} columns)")
    lines.append("-" * 70)
    for col in df.columns:
        lines.append(f"  {col}")
    lines.append("")

    lines.append("SAMPLE ROWS (TOP 5)")
    lines.append("-" * 70)
    lines.append(df.to_string(index=False))

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Saved: {REPORT_PATH}")


if __name__ == "__main__":
    main()
