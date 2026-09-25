"""
فاز ۱ — بخش «الف: توصیفی پایه» از فهرست پیشنهادی تحلیل‌ها (docs/EXECUTION_LOG.md، ۲۰۲۶-۰۹-۰۳):

۱. توزیع نوع تسهیلات (گروه‌بندی‌شده) و سهم هرکدام از مانده‌ی کل
۲. هیستوگرام اندازه‌ی تسهیلات (خرد/متوسط/کلان)
۳. رتبه‌بندی Top-N شعب بر اساس حجم تسهیلات و سود پرداختی سپرده
۴. نرخ رشد سالانه‌ی مانده‌ی سپرده و تسهیلات (YoY)
۵. نسبت تسهیلات به سپرده (Loan-to-Deposit Ratio) در طول زمان
۶. توزیع جغرافیایی (شهر) تسهیلات و سود پرداختی سپرده

⚠️ نکات مهمی که باید رعایت شوند (تجربه‌ی این پروژه):
- هرگز مستقیم روی Loan_Remain/Loan_Contract_Info خام SUM/COUNT نزنید — هر دو تکرار دارند
  (چندضامنی و تکرار رکورد؛ رجوع به docs/08_data_landscape_report.md و reports/data_profile/Table_Profiles.xlsx).
  همیشه از vw_Loan_Contract_Dedup و منطق یک‌ردیف‌سازی مشابه vw_Loan_Remain_By_Branch_Month استفاده کنید.
- بخش «رتبه‌بندی شعب» و «توزیع جغرافیایی» سپرده محدودیت دارند: هیچ جدولی مستقیماً حساب سپرده را به شعبه
  وصل نمی‌کند (Customer_Profile.creator_branch ایزوله است). به‌جای مانده‌ی سپرده، از سود پرداختی سپرده
  به تفکیک شعبه (Interset_branch_sum) به‌عنوان یک پروکسی معقول استفاده شده — این محدودیت در کد و
  خروجی صراحتاً یادداشت شده.
- گروه‌بندی نوع تسهیلات و بازه‌های اندازه‌ی تسهیلات، دسته‌بندی‌های نمایشیِ این تحلیل‌اند، نه
  طبقه‌بندی رسمی بانک — اگر بانک آستانه‌ی رسمی خرد/متوسط/کلان اعلام کند، باید جایگزین شود.

خروجی: ۶ نمودار PNG در reports/figures/phase1_market_overview/ و ۶ فایل CSV در data/processed/phase1_market_overview/
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from tt_bank.common.persian_plot import fa, setup_persian_font, to_persian_digits
from tt_bank.db.connection import get_engine

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures" / "phase1_market_overview"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "phase1_market_overview"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
setup_persian_font()

LATEST_LOAN_TD = 14041229   # آخرین Transaction_Date در Loan_Remain (اسفند ۱۴۰۴)
LATEST_MONTH = 140412       # آخرین year_month/year_mount مشترک


def save_barh(df: pd.DataFrame, label_col: str, value_col: str, title: str, xlabel: str, filename: str) -> None:
    """کمکی مشترک: نمودار میله‌ای افقی با فونت فارسی + اعداد فارسی روی محور x."""
    fig, ax = plt.subplots(figsize=(10, max(4, 0.5 * len(df))))
    y_pos = range(len(df))
    ax.barh(y_pos, df[value_col])
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels([fa(t) for t in df[label_col]], fontsize=10)
    ax.set_xlabel(fa(xlabel))
    ax.set_title(fa(title))
    ax.xaxis.set_major_formatter(lambda v, pos: to_persian_digits(f"{v:,.0f}"))
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / filename, dpi=150)
    plt.close(fig)


def section_1_loan_type_distribution(engine) -> None:
    """۱. توزیع نوع تسهیلات (گروه‌بندی‌شده) و سهم از مانده‌ی کل، آخرین ماه.

    ⚠️ رفع باگ پوشش (بازبینی مستقل Claude Opus، ۲۰۲۶-۰۹-۱۱، بند ۲.۷): نسخه‌ی اول با INNER JOIN به
    vw_Loan_Contract_Dedup، ۲۲.۴٪ از مانده‌ی کل تسهیلات (قراردادهایی که در Loan_Contract_Info رکورد
    ندارند — همان یافته‌ی «orphan» بخش ت) را بی‌صدا از نمودار حذف می‌کرد؛ نمودار طوری به‌نظر می‌رسید که
    انگار ۱۰۰٪ پرتفوی طبقه‌بندی شده. رفع با LEFT JOIN + سطل صریح «نامشخص (بدون رکورد قرارداد)».
    """
    query = f"""
        WITH LatestRemain AS (
            SELECT loanfile_id, Total_Remain,
                   ROW_NUMBER() OVER (PARTITION BY loanfile_id ORDER BY customer_id) AS rn
            FROM dbo.Loan_Remain
            WHERE Transaction_Date = {LATEST_LOAN_TD}
        )
        SELECT
            CASE
                WHEN c.loan_type_description LIKE N'%قرض الحسنه%'    THEN N'قرض‌الحسنه'
                WHEN c.loan_type_description LIKE N'%مرابحه%'        THEN N'مرابحه'
                WHEN c.loan_type_description LIKE N'%مشارکت مدني%'   THEN N'مشارکت مدنی'
                WHEN c.loan_type_description LIKE N'%فروش اقساطي%'   THEN N'فروش اقساطی'
                WHEN c.loan_type_description LIKE N'%جعاله%'         THEN N'جعاله'
                WHEN c.loan_type_description LIKE N'%مضاربه%'        THEN N'مضاربه'
                WHEN c.loan_type_description LIKE N'%استصناع%'       THEN N'استصناع'
                WHEN c.loan_type_description IS NULL                THEN N'نامشخص (بدون رکورد قرارداد)'
                ELSE N'سایر'
            END AS loan_type_group,
            COUNT(DISTINCT lr.loanfile_id) AS loan_count,
            SUM(lr.Total_Remain)           AS total_balance
        FROM LatestRemain lr
        LEFT JOIN dbo.vw_Loan_Contract_Dedup c ON c.loanfile_id = lr.loanfile_id
        WHERE lr.rn = 1
        GROUP BY
            CASE
                WHEN c.loan_type_description LIKE N'%قرض الحسنه%'    THEN N'قرض‌الحسنه'
                WHEN c.loan_type_description LIKE N'%مرابحه%'        THEN N'مرابحه'
                WHEN c.loan_type_description LIKE N'%مشارکت مدني%'   THEN N'مشارکت مدنی'
                WHEN c.loan_type_description LIKE N'%فروش اقساطي%'   THEN N'فروش اقساطی'
                WHEN c.loan_type_description LIKE N'%جعاله%'         THEN N'جعاله'
                WHEN c.loan_type_description LIKE N'%مضاربه%'        THEN N'مضاربه'
                WHEN c.loan_type_description LIKE N'%استصناع%'       THEN N'استصناع'
                WHEN c.loan_type_description IS NULL                THEN N'نامشخص (بدون رکورد قرارداد)'
                ELSE N'سایر'
            END
        ORDER BY total_balance DESC
    """
    df = pd.read_sql(query, engine)
    df["balance_share_pct"] = (df["total_balance"] / df["total_balance"].sum() * 100).round(2)
    print("\n=== ۱. توزیع نوع تسهیلات (گروه‌بندی‌شده، آخرین ماه، شامل سطل «نامشخص») ===")
    print(df.to_string(index=False))
    unknown_pct = df.loc[df["loan_type_group"] == "نامشخص (بدون رکورد قرارداد)", "balance_share_pct"].sum()
    print(f"→ {unknown_pct:.1f}٪ از مانده‌ی کل تسهیلات فاقد رکورد در Loan_Contract_Info است (یافته‌ی «orphan»، بخش ت این پروژه) — این سهم در نمودار هم صریحاً نشان داده می‌شود.")
    if not df.empty:
        save_barh(df, "loan_type_group", "total_balance",
                   f"توزیع مانده‌ی تسهیلات به تفکیک نوع — ماه {to_persian_digits(LATEST_MONTH)}",
                   "مانده کل (ریال)", "loan_type_distribution.png")
    df.to_csv(PROCESSED_DIR / "loan_type_distribution.csv", index=False)


def section_2_loan_size_histogram(engine) -> None:
    """۲. هیستوگرام اندازه‌ی تسهیلات بر اساس مبلغ اعطایی (GRANT_AMOUNT) — بازه‌های نمایشی."""
    query = """
        SELECT
            CASE
                WHEN grant_amount < 500000000        THEN N'۱) زیر ۵۰۰ میلیون'
                WHEN grant_amount < 2000000000       THEN N'۲) ۵۰۰م تا ۲ میلیارد'
                WHEN grant_amount < 10000000000      THEN N'۳) ۲ تا ۱۰ میلیارد'
                WHEN grant_amount < 50000000000      THEN N'۴) ۱۰ تا ۵۰ میلیارد'
                ELSE                                       N'۵) بالای ۵۰ میلیارد'
            END AS size_bucket,
            COUNT(*)             AS loan_count,
            SUM(grant_amount)    AS total_granted
        FROM dbo.vw_Loan_Contract_Dedup
        WHERE grant_amount IS NOT NULL AND grant_amount > 0
        GROUP BY
            CASE
                WHEN grant_amount < 500000000        THEN N'۱) زیر ۵۰۰ میلیون'
                WHEN grant_amount < 2000000000       THEN N'۲) ۵۰۰م تا ۲ میلیارد'
                WHEN grant_amount < 10000000000      THEN N'۳) ۲ تا ۱۰ میلیارد'
                WHEN grant_amount < 50000000000      THEN N'۴) ۱۰ تا ۵۰ میلیارد'
                ELSE                                       N'۵) بالای ۵۰ میلیارد'
            END
        ORDER BY size_bucket
    """
    df = pd.read_sql(query, engine)
    print("\n=== ۲. هیستوگرام اندازه‌ی تسهیلات (بر اساس مبلغ اعطایی، بازه‌های نمایشی) ===")
    print(df.to_string(index=False))
    if not df.empty:
        fig, ax = plt.subplots(figsize=(10, 6))
        x_pos = range(len(df))
        ax.bar(list(x_pos), df["loan_count"])
        ax.set_xticks(list(x_pos))
        ax.set_xticklabels([fa(t) for t in df["size_bucket"]], rotation=20, ha="right")
        ax.set_ylabel(fa("تعداد قرارداد"))
        ax.set_title(fa("توزیع تعداد تسهیلات بر اساس اندازه‌ی مبلغ اعطایی (بازه‌های نمایشی)"))
        ax.yaxis.set_major_formatter(lambda v, pos: to_persian_digits(f"{v:,.0f}"))
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / "loan_size_histogram.png", dpi=150)
        plt.close(fig)
    df.to_csv(PROCESSED_DIR / "loan_size_histogram.csv", index=False)


def section_3_top_branches(engine) -> None:
    """۳. رتبه‌بندی Top-10 شعب: (الف) حجم مانده‌ی تسهیلات، (ب) سود پرداختی سپرده (پروکسیِ حجم سپرده)."""
    loans = pd.read_sql(
        f"""
        SELECT TOP 10 branch_name, SUM(total_balance) AS total_loan_balance
        FROM dbo.vw_Loan_Remain_By_Branch_Month
        WHERE year_month = {LATEST_MONTH} AND branch_name IS NOT NULL
        GROUP BY branch_name
        ORDER BY total_loan_balance DESC
        """,
        engine,
    )
    print("\n=== ۳.الف Top-10 شعب بر اساس مانده‌ی تسهیلات (آخرین ماه) ===")
    print(loans.to_string(index=False))
    if not loans.empty:
        save_barh(loans.iloc[::-1], "branch_name", "total_loan_balance",
                   f"Top-10 شعب بر اساس مانده‌ی تسهیلات — ماه {to_persian_digits(LATEST_MONTH)}",
                   "مانده‌ی تسهیلات (ریال)", "top_branches_by_loan.png")
    loans.to_csv(PROCESSED_DIR / "top_branches_by_loan.csv", index=False)

    # ⚠️ پروکسی: مانده‌ی سپرده به شعبه وصل نیست؛ سود پرداختی سپرده (که شعبه دارد) جایگزین شده.
    deposit_interest = pd.read_sql(
        """
        SELECT TOP 10 b.branch_name, SUM(ibs.Amount) AS total_deposit_interest_paid
        FROM dbo.Interset_branch_sum ibs
        JOIN dbo.vw_Branch_Dim b
            ON b.branch_code = LTRIM(RTRIM(REPLACE(REPLACE(ibs.BranchCode, CHAR(13), ''), CHAR(10), '')))
        WHERE REPLACE(REPLACE(ibs.Year_Mounth, CHAR(13), ''), CHAR(10), '') = '1404/12'
        GROUP BY b.branch_name
        ORDER BY total_deposit_interest_paid DESC
        """,
        engine,
    )
    print("\n=== ۳.ب Top-10 شعب بر اساس سود پرداختی سپرده (پروکسیِ حجم سپرده — آخرین ماه) ===")
    print(deposit_interest.to_string(index=False))
    if not deposit_interest.empty:
        save_barh(deposit_interest.iloc[::-1], "branch_name", "total_deposit_interest_paid",
                   f"Top-10 شعب بر اساس سود پرداختی سپرده — ماه {to_persian_digits(LATEST_MONTH)}",
                   "سود پرداختی سپرده (ریال)", "top_branches_by_deposit_interest.png")
    deposit_interest.to_csv(PROCESSED_DIR / "top_branches_by_deposit_interest.csv", index=False)


def section_4_yoy_growth(engine) -> None:
    """۴. نرخ رشد سالانه (YoY) مانده‌ی سپرده و تسهیلات — بر اساس مانده‌ی پایان اسفند هر سال."""
    # ⚠️ نکته‌ی تکرارشونده‌ی این پروژه: year_mount/year_month از نوع numeric است؛ تقسیم بدون CAST به
    # bigint نتیجه‌ی اعشاری می‌دهد (نه تقسیم صحیح) — رجوع به docs/06_phase1_sql_views.md.
    deposit_yearly = pd.read_sql(
        """
        SELECT CAST(year_mount AS bigint) / 100 AS shamsi_year,
               SUM(account_count * avg_balance) AS total_deposit_balance
        FROM dbo.vw_Deposit_Portfolio_Monthly
        WHERE CAST(year_mount AS bigint) % 100 = 12
        GROUP BY CAST(year_mount AS bigint) / 100
        ORDER BY shamsi_year
        """,
        engine,
    )
    loan_yearly = pd.read_sql(
        """
        SELECT CAST(year_month AS bigint) / 100 AS shamsi_year, SUM(total_balance) AS total_loan_balance
        FROM dbo.vw_Loan_Remain_By_Branch_Month
        WHERE CAST(year_month AS bigint) % 100 = 12
        GROUP BY CAST(year_month AS bigint) / 100
        ORDER BY shamsi_year
        """,
        engine,
    )
    merged = deposit_yearly.merge(loan_yearly, on="shamsi_year", how="outer").sort_values("shamsi_year")
    merged["deposit_yoy_pct"] = merged["total_deposit_balance"].pct_change().mul(100).round(1)
    merged["loan_yoy_pct"] = merged["total_loan_balance"].pct_change().mul(100).round(1)
    print("\n=== ۴. رشد سالانه‌ی مانده‌ی سپرده و تسهیلات (پایان اسفند هر سال) ===")
    print(merged.to_string(index=False))

    if not merged.empty:
        fig, ax = plt.subplots(figsize=(9, 5))
        x_pos = range(len(merged))
        x_labels = [to_persian_digits(int(y)) for y in merged["shamsi_year"]]
        ax.bar([p - 0.2 for p in x_pos], merged["deposit_yoy_pct"], width=0.4, label=fa("رشد سپرده"))
        ax.bar([p + 0.2 for p in x_pos], merged["loan_yoy_pct"], width=0.4, label=fa("رشد تسهیلات"))
        ax.set_xticks(list(x_pos))
        ax.set_xticklabels(x_labels)
        ax.set_ylabel(fa("درصد رشد نسبت به سال قبل"))
        ax.set_title(fa("نرخ رشد سالانه‌ی مانده‌ی سپرده و تسهیلات (YoY)"))
        ax.yaxis.set_major_formatter(lambda v, pos: to_persian_digits(f"{v:,.0f}") + "%")
        ax.axhline(0, color="black", linewidth=0.8)
        ax.legend(prop={"family": "Vazirmatn"})
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / "yoy_growth.png", dpi=150)
        plt.close(fig)
    merged.to_csv(PROCESSED_DIR / "yoy_growth.csv", index=False)


def section_5_loan_to_deposit_ratio(engine) -> None:
    """۵. نسبت تسهیلات به سپرده (LDR) در طول زمان — فقط بازه‌ی مشترک دو جدول (۱۴۰۰/۰۱ تا ۱۴۰۴/۱۲، ۶۰ ماه)."""
    deposit_m = pd.read_sql(
        """
        SELECT year_mount, SUM(account_count * avg_balance) AS total_deposit_balance
        FROM dbo.vw_Deposit_Portfolio_Monthly
        WHERE year_mount >= 140001
        GROUP BY year_mount
        """,
        engine,
    )
    loan_m = pd.read_sql(
        """
        SELECT year_month AS year_mount, SUM(total_balance) AS total_loan_balance
        FROM dbo.vw_Loan_Remain_By_Branch_Month
        GROUP BY year_month
        """,
        engine,
    )
    ldr = deposit_m.merge(loan_m, on="year_mount", how="inner").sort_values("year_mount")
    ldr["ldr_pct"] = (ldr["total_loan_balance"] / ldr["total_deposit_balance"] * 100).round(1)
    print("\n=== ۵. نسبت تسهیلات به سپرده - LDR (نمونه ۵ ماه اول/آخر) ===")
    print(pd.concat([ldr.head(), ldr.tail()]).to_string(index=False))

    if not ldr.empty:
        fig, ax = plt.subplots(figsize=(12, 5))
        x_pos = range(len(ldr))
        x_labels = [to_persian_digits(v) for v in ldr["year_mount"].astype(int).astype(str)]
        ax.plot(list(x_pos), ldr["ldr_pct"])
        ax.set_xticks(list(x_pos))
        ax.set_xticklabels(x_labels, rotation=90, fontsize=6)
        ax.set_title(fa("نسبت تسهیلات به سپرده (Loan-to-Deposit Ratio) در طول زمان"))
        ax.set_xlabel(fa("ماه (شمسی YYYYMM)"))
        ax.set_ylabel(fa("درصد"))
        ax.yaxis.set_major_formatter(lambda v, pos: to_persian_digits(f"{v:,.0f}") + "%")
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / "loan_to_deposit_ratio.png", dpi=150)
        plt.close(fig)
    ldr.to_csv(PROCESSED_DIR / "loan_to_deposit_ratio.csv", index=False)


def section_6_geographic_distribution(engine) -> None:
    """۶. توزیع جغرافیایی (شهر): مانده‌ی تسهیلات (کامل) و سود پرداختی سپرده (پروکسی سپرده)، آخرین ماه."""
    loan_geo = pd.read_sql(
        f"""
        SELECT TOP 15 city_name, SUM(total_balance) AS total_loan_balance
        FROM dbo.vw_Loan_Remain_By_Branch_Month
        WHERE year_month = {LATEST_MONTH} AND city_name IS NOT NULL
        GROUP BY city_name
        ORDER BY total_loan_balance DESC
        """,
        engine,
    )
    print("\n=== ۶.الف توزیع جغرافیایی مانده‌ی تسهیلات به تفکیک شهر (Top-15، آخرین ماه) ===")
    print(loan_geo.to_string(index=False))
    if not loan_geo.empty:
        save_barh(loan_geo.iloc[::-1], "city_name", "total_loan_balance",
                   f"توزیع جغرافیایی مانده‌ی تسهیلات (Top-15 شهر) — ماه {to_persian_digits(LATEST_MONTH)}",
                   "مانده‌ی تسهیلات (ریال)", "geographic_distribution_loans.png")
    loan_geo.to_csv(PROCESSED_DIR / "geographic_distribution_loans.csv", index=False)


def main() -> None:
    engine = get_engine()
    section_1_loan_type_distribution(engine)
    section_2_loan_size_histogram(engine)
    section_3_top_branches(engine)
    section_4_yoy_growth(engine)
    section_5_loan_to_deposit_ratio(engine)
    section_6_geographic_distribution(engine)
    print(f"\nهمه‌ی خروجی‌های بخش الف در {PROCESSED_DIR} و {FIGURES_DIR} ذخیره شدند.")


if __name__ == "__main__":
    main()
