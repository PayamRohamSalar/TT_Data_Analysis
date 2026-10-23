"""
practitioner_count raw statistical extraction - Legal Entities only (Customer_Profile).
Output: results/practitioner_count_raw_stats.txt
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from db_config import get_engine

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
REPORT_PATH = os.path.join(RESULTS_DIR, "practitioner_count_raw_stats.txt")

CLEAN_REAL_OR_LEGAL_SQL = "LTRIM(RTRIM(REPLACE(real_or_legal, CHAR(34), '')))"
CLEAN_PRACTITIONER_SQL = (
    "LTRIM(RTRIM(REPLACE(REPLACE(practitioner_count, CHAR(13), ''), CHAR(34), '')))"
)
LEGAL = "حقوقي"

PERCENTILES = [0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99, 0.995, 0.999]


def fetch_legal_practitioner_count(engine) -> pd.DataFrame:
    query = f"""
        SELECT Customer_id, {CLEAN_PRACTITIONER_SQL} AS pc_clean
        FROM Customer_Profile
        WHERE {CLEAN_REAL_OR_LEGAL_SQL} = N'{LEGAL}'
    """
    return pd.read_sql(query, engine)


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    engine = get_engine()

    df = fetch_legal_practitioner_count(engine)
    total = len(df)

    numeric_mask = df["pc_clean"].str.match(r"^\d+$")
    blank_mask = df["pc_clean"] == ""
    non_numeric_non_blank_mask = ~numeric_mask & ~blank_mask

    numeric_df = df.loc[numeric_mask].copy()
    numeric_df["pc_value"] = pd.to_numeric(numeric_df["pc_clean"]).astype("int64")

    null_blank_count = int(blank_mask.sum())
    non_numeric_count = int(non_numeric_non_blank_mask.sum())
    numeric_count = int(numeric_mask.sum())

    percentile_values = numeric_df["pc_value"].quantile(PERCENTILES)
    desc_min = numeric_df["pc_value"].min()
    desc_max = numeric_df["pc_value"].max()
    desc_mean = numeric_df["pc_value"].mean()
    desc_std = numeric_df["pc_value"].std()

    top50 = numeric_df.sort_values("pc_value", ascending=False).head(50)[
        ["Customer_id", "pc_value"]
    ]

    lines = []
    lines.append("practitioner_count - Raw Statistical Extraction (Legal Entities only)")
    lines.append("=" * 70)
    lines.append(f"Generated at: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    lines.append("RECORD COUNTS")
    lines.append("-" * 70)
    lines.append(f"Total legal-entity records: {total}")
    lines.append(f"Numeric records: {numeric_count}")
    lines.append(f"Null/Blank records: {null_blank_count}")
    lines.append(f"Non-numeric (non-blank) records: {non_numeric_count}")
    lines.append("")

    lines.append("DESCRIPTIVE STATISTICS (numeric records only)")
    lines.append("-" * 70)
    lines.append(f"Min: {desc_min}")
    lines.append(f"Max: {desc_max}")
    lines.append(f"Mean: {desc_mean}")
    lines.append(f"StdDev: {desc_std}")
    lines.append("")

    lines.append("PERCENTILES (numeric records only)")
    lines.append("-" * 70)
    for p in PERCENTILES:
        lines.append(f"P{p*100:g}: {percentile_values[p]}")
    lines.append("")

    lines.append("TOP 50 OUTLIERS (highest practitioner_count values)")
    lines.append("-" * 70)
    lines.append(f"{'Customer_id':>20} {'practitioner_count':>20}")
    for _, row in top50.iterrows():
        lines.append(f"{int(row['Customer_id']):>20} {row['pc_value']:>20}")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Saved: {REPORT_PATH}")


if __name__ == "__main__":
    main()
