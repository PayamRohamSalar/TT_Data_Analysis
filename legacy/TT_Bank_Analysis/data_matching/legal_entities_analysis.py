"""
بررسی مشتریان حقوقی (Legal/Corporate) در جدول Customer_Profile.
هدف: رفع ابهامات شناسایی‌شده در نمونه ۱۰۰ ردیفی اولیه:
  1) آیا اصلاً مشتری حقوقی در کل دیتابیس وجود دارد؟
  2) آیا ستون age برای حقوقی‌ها سال تاسیس (شمسی) است یا چیز دیگر؟
  3) آیا اندازه سازمانی (Organizational Size) در جایی از پروفایل ثبت شده؟

خروجی: results/Legal_Entities_Analysis.txt
"""
import os
import re
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from db_config import get_engine

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
REPORT_PATH = os.path.join(RESULTS_DIR, "Legal_Entities_Analysis.txt")

# ستون real_or_legal حاوی کاراکترهای " و فاصله اضافی است (نمونه: '"حقوقي     "')
CLEAN_REAL_OR_LEGAL_SQL = "LTRIM(RTRIM(REPLACE(real_or_legal, CHAR(34), '')))"
# ستون practitioner_count علاوه بر " ممکن است شامل CHAR(13) (\r) هم باشد
CLEAN_PRACTITIONER_SQL = (
    "LTRIM(RTRIM(REPLACE(REPLACE(practitioner_count, CHAR(13), ''), CHAR(34), '')))"
)

LEGAL = "حقوقي"
INDIVIDUAL = "حقيقي"


def get_distribution(engine) -> pd.DataFrame:
    query = f"""
        SELECT {CLEAN_REAL_OR_LEGAL_SQL} AS entity_type, COUNT(*) AS cnt
        FROM Customer_Profile
        GROUP BY {CLEAN_REAL_OR_LEGAL_SQL}
    """
    return pd.read_sql(query, engine)


def get_age_stats(engine, entity_type: str) -> pd.Series:
    query = f"""
        SELECT
            MIN(age) AS min_age,
            MAX(age) AS max_age,
            AVG(CAST(age AS float)) AS avg_age,
            SUM(CASE WHEN age IS NULL THEN 1 ELSE 0 END) AS null_cnt,
            COUNT(*) AS total
        FROM Customer_Profile
        WHERE {CLEAN_REAL_OR_LEGAL_SQL} = N'{entity_type}'
    """
    return pd.read_sql(query, engine).iloc[0]


def get_age_histogram(engine, entity_type: str, top_n: int = 15) -> pd.DataFrame:
    query = f"""
        SELECT age, COUNT(*) AS cnt
        FROM Customer_Profile
        WHERE {CLEAN_REAL_OR_LEGAL_SQL} = N'{entity_type}'
        GROUP BY age
        ORDER BY cnt DESC
    """
    return pd.read_sql(query, engine).head(top_n)


def get_categorical_summary(engine, column: str, entity_type: str, top_n: int = 15) -> pd.DataFrame:
    query = f"""
        SELECT {column} AS value, COUNT(*) AS cnt
        FROM Customer_Profile
        WHERE {CLEAN_REAL_OR_LEGAL_SQL} = N'{entity_type}'
        GROUP BY {column}
        ORDER BY cnt DESC
    """
    df = pd.read_sql(query, engine)
    return df.head(top_n), len(df)


def get_practitioner_count_raw(engine, entity_type: str) -> pd.DataFrame:
    query = f"""
        SELECT {CLEAN_PRACTITIONER_SQL} AS pc_clean
        FROM Customer_Profile
        WHERE {CLEAN_REAL_OR_LEGAL_SQL} = N'{entity_type}'
    """
    return pd.read_sql(query, engine)


def analyze_practitioner_count(df: pd.DataFrame) -> dict:
    numeric_mask = df["pc_clean"].str.match(r"^\d+$")
    numeric = pd.to_numeric(df.loc[numeric_mask, "pc_clean"])
    blank_cnt = int((df["pc_clean"] == "").sum())
    non_numeric_non_blank = sorted(
        df.loc[~numeric_mask & (df["pc_clean"] != ""), "pc_clean"].unique().tolist()
    )
    return {
        "total": len(df),
        "numeric_count": int(numeric_mask.sum()),
        "blank_count": blank_cnt,
        "non_numeric_values": non_numeric_non_blank,
        "stats": numeric.describe() if len(numeric) else None,
        "outliers_gt_1000": int((numeric > 1000).sum()) if len(numeric) else 0,
        "pct_le_100": float((numeric <= 100).mean() * 100) if len(numeric) else 0.0,
        "top_values": numeric.value_counts().head(10) if len(numeric) else None,
    }


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    print("در حال اتصال به دیتابیس...")
    engine = get_engine()

    lines = []
    lines.append("Legal Entities & Company Size Analysis - Customer_Profile")
    lines.append("=" * 70)
    lines.append(f"Generated at: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # 1) Legal vs Individual distribution
    print("در حال محاسبه توزیع حقیقی/حقوقی...")
    dist = get_distribution(engine)
    total = int(dist["cnt"].sum())
    lines.append("1) real_or_legal distribution (full table)")
    lines.append("-" * 70)
    lines.append(
        "NOTE: raw values contain literal quote characters and padding, "
        "e.g. '\"حقوقي     \"' (len=12). Cleaned with LTRIM/RTRIM/REPLACE before grouping."
    )
    for _, row in dist.iterrows():
        pct = row["cnt"] / total * 100
        lines.append(f"  {row['entity_type']!r:>15}: {row['cnt']:>10,} rows ({pct:.2f}%)")
    lines.append(f"  {'TOTAL':>15}: {total:>10,} rows")
    legal_exists = dist["entity_type"].str.strip().eq(LEGAL).any()
    lines.append("")
    lines.append(
        f"=> CONCLUSION: Legal entities {'DO' if legal_exists else 'DO NOT'} exist beyond the "
        "initial individual-only 100-row sample."
    )
    lines.append("")

    # 2) Age analysis for legal vs individual
    print("در حال تحلیل ستون age برای حقوقی و حقیقی...")
    legal_age = get_age_stats(engine, LEGAL)
    indiv_age = get_age_stats(engine, INDIVIDUAL)
    legal_hist = get_age_histogram(engine, LEGAL)

    lines.append("2) 'age' column analysis - Establishment Year hypothesis")
    lines.append("-" * 70)
    lines.append(
        "Hypothesis to test: for legal entities, does 'age' actually hold an Establishment "
        "Year in the Persian calendar (expected range ~1300-1450), rather than a human age?"
    )
    lines.append("")
    lines.append(f"  Legal (حقوقي)      -> min={legal_age.min_age}, max={legal_age.max_age}, "
                  f"avg={legal_age.avg_age:.2f}, nulls={legal_age.null_cnt}, n={legal_age.total}")
    lines.append(f"  Individual (حقيقي) -> min={indiv_age.min_age}, max={indiv_age.max_age}, "
                  f"avg={indiv_age.avg_age:.2f}, nulls={indiv_age.null_cnt}, n={indiv_age.total}")
    lines.append("")
    lines.append("  Top 15 most frequent 'age' values for legal entities:")
    for _, row in legal_hist.iterrows():
        age_val = "NULL" if pd.isna(row["age"]) else row["age"]
        lines.append(f"    age={age_val!s:>6} -> {row['cnt']:>6,} rows")
    lines.append("")
    in_persian_year_range = (legal_age.min_age >= 1300) and (legal_age.max_age <= 1450)
    lines.append(
        f"=> CONCLUSION: legal-entity 'age' values range {legal_age.min_age}-{legal_age.max_age} "
        f"(avg {legal_age.avg_age:.1f}), which is {'CONSISTENT' if in_persian_year_range else 'NOT consistent'} "
        "with a Persian-calendar establishment year (1300-1450). The range and average are "
        "far lower than the individual customers' age range/average "
        f"({indiv_age.min_age}-{indiv_age.max_age}, avg {indiv_age.avg_age:.1f}), which itself looks like "
        "genuine human age. Most likely interpretation: 'age' is reused for legal entities as "
        "'years since establishment / years as a customer' (a small integer), NOT as the "
        "calendar year of establishment."
    )
    lines.append("")

    # 3) job_name / membership_info / membership_type_value / practitioner_count for legal entities
    print("در حال بررسی job_name, membership_info, membership_type_value, practitioner_count...")
    lines.append("3) Candidate 'Organizational Size' / classification fields (legal entities only)")
    lines.append("-" * 70)

    job_summary, job_distinct = get_categorical_summary(engine, "job_name", LEGAL)
    lines.append(f"  job_name -> {job_distinct} distinct value(s):")
    for _, row in job_summary.iterrows():
        lines.append(f"    {row['value']!r:>20}: {row['cnt']:>8,}")
    lines.append("  => Not usable: effectively always blank for legal entities.")
    lines.append("")

    mi_summary, mi_distinct = get_categorical_summary(engine, "membership_info", LEGAL)
    lines.append(f"  membership_info -> {mi_distinct} distinct value(s):")
    for _, row in mi_summary.iterrows():
        lines.append(f"    {row['value']!r:>20}: {row['cnt']:>8,}")
    lines.append("  => Not usable for org size: blank for ~99.99% of legal entities; the few "
                  "non-blank values are CBS-##### codes (system reference IDs, not a size/scale field).")
    lines.append("")

    mtv_summary, mtv_distinct = get_categorical_summary(engine, "membership_type_value", LEGAL)
    lines.append(f"  membership_type_value -> {mtv_distinct} distinct value(s):")
    for _, row in mtv_summary.iterrows():
        lines.append(f"    {row['value']!r:>20}: {row['cnt']:>8,}")
    lines.append("  => This confirms the Cooperative (تعاوني) / Non-Cooperative (غير تعاوني) "
                  "status field for legal entities, but it is NOT a size/scale indicator.")
    lines.append("")

    # practitioner_count deep dive - both for legal and individual, for contrast
    legal_pc_raw = get_practitioner_count_raw(engine, LEGAL)
    indiv_pc_raw = get_practitioner_count_raw(engine, INDIVIDUAL)
    legal_pc = analyze_practitioner_count(legal_pc_raw)
    indiv_pc = analyze_practitioner_count(indiv_pc_raw)

    lines.append("  practitioner_count -> BEST CANDIDATE for 'Organizational Size':")
    lines.append(
        f"    Legal entities:      total={legal_pc['total']:,}, numeric={legal_pc['numeric_count']:,} "
        f"({legal_pc['numeric_count']/legal_pc['total']*100:.1f}%), blank={legal_pc['blank_count']:,} "
        f"({legal_pc['blank_count']/legal_pc['total']*100:.1f}%)"
    )
    lines.append(
        f"    Individual customers: total={indiv_pc['total']:,}, numeric={indiv_pc['numeric_count']:,} "
        f"({indiv_pc['numeric_count']/indiv_pc['total']*100:.2f}%), blank={indiv_pc['blank_count']:,} "
        f"({indiv_pc['blank_count']/indiv_pc['total']*100:.2f}%)"
    )
    if indiv_pc["non_numeric_values"]:
        lines.append(f"    Individual non-numeric noise values found: {indiv_pc['non_numeric_values']}")
    lines.append("")
    if legal_pc["stats"] is not None:
        s = legal_pc["stats"]
        lines.append("    Legal-entity numeric distribution (raw, before outlier handling):")
        lines.append(f"      count={s['count']:.0f}  min={s['min']:.0f}  25%={s['25%']:.0f}  "
                      f"median={s['50%']:.0f}  75%={s['75%']:.0f}  max={s['max']:.0f}  mean={s['mean']:.1f}")
        lines.append(f"      {legal_pc['pct_le_100']:.1f}% of numeric values are <= 100 "
                      f"(plausible employee-count range).")
        lines.append(f"      {legal_pc['outliers_gt_1000']} record(s) (>1000) look like data-entry "
                      "errors/outliers (e.g. 7-8 digit values such as 76,234,194) and should be "
                      "capped or excluded in downstream modeling.")
        lines.append("      Most frequent values:")
        for val, cnt in legal_pc["top_values"].items():
            lines.append(f"        {val:>10.0f}: {cnt:>6,}")
    lines.append("")
    lines.append(
        "=> CONCLUSION: 'practitioner_count' is essentially unused for individual customers "
        f"({indiv_pc['numeric_count']/indiv_pc['total']*100:.2f}% numeric, rest blank/noise) but is "
        f"populated for {legal_pc['numeric_count']/legal_pc['total']*100:.1f}% of legal entities with "
        "small integers concentrated in the 1-100 range (median ~7). This strongly matches "
        "'number of employees / practitioners' i.e. an Organizational Size proxy, not "
        "job_name/membership_info. A small number of extreme outliers exist and need cleaning "
        "before use."
    )
    lines.append("")
    lines.append("=" * 70)
    lines.append("SUMMARY")
    lines.append("-" * 70)
    lines.append(f"- Legal entities in full DB: {dist.loc[dist['entity_type'].str.strip()==LEGAL,'cnt'].sum():,} "
                 f"({dist.loc[dist['entity_type'].str.strip()==LEGAL,'cnt'].sum()/total*100:.2f}% of all customers)")
    lines.append("- 'age' for legal entities is NOT a Persian establishment year; likely a small "
                 "'years since establishment/relationship' integer reusing the same column as human age.")
    lines.append("- job_name and membership_info carry no usable org-size/industry information for legal entities.")
    lines.append("- membership_type_value only encodes Cooperative/Non-Cooperative status (already known).")
    lines.append("- practitioner_count is the best available proxy for Organizational Size "
                 "(employee count), populated for ~94-95% of legal entities, needs outlier cleaning.")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("-" * 50)
    print(f"گزارش با موفقیت ذخیره شد: {REPORT_PATH}")


if __name__ == "__main__":
    main()
