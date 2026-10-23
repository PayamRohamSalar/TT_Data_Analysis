"""
Branch code extraction and aggregation - Customer_Profile.creator_branch.
Output: results/Unique_Branch_Codes.xlsx (+ schema-check note in console/log)
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from db_config import get_engine

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
OUTPUT_XLSX = os.path.join(RESULTS_DIR, "Unique_Branch_Codes.xlsx")


def check_branch_columns(engine) -> pd.DataFrame:
    query = """
        SELECT TABLE_NAME, COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'dbo' AND COLUMN_NAME LIKE '%branch%'
    """
    return pd.read_sql(query, engine)


def get_branch_distribution(engine) -> pd.DataFrame:
    query = """
        SELECT creator_branch AS Branch_Code, COUNT(Customer_id) AS Total_Customers
        FROM Customer_Profile
        GROUP BY creator_branch
        ORDER BY Total_Customers DESC
    """
    return pd.read_sql(query, engine)


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    engine = get_engine()

    branch_cols = check_branch_columns(engine)
    print("Columns with 'branch' in name across dbo schema:")
    print(branch_cols.to_string(index=False))

    dist_df = get_branch_distribution(engine)
    dist_df.to_excel(OUTPUT_XLSX, index=False)

    print(f"Total unique branch codes: {len(dist_df)}")
    print(f"Saved: {OUTPUT_XLSX}")


if __name__ == "__main__":
    main()
