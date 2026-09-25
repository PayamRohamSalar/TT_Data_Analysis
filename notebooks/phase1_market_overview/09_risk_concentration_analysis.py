"""
فاز ۱ — تحلیل تمرکز ریسک (پیشنهاد بازبینی مستقل Claude Opus، ۲۰۲۶-۰۹-۱۱، بند ۳.ب موارد ۱۱ و ۱۳):

۱. تمرکز تک‌نامی (Single-name concentration): مانده و وضعیت NPL بزرگ‌ترین مشتریان تسهیلاتی —
   «مهم‌ترین جدول برای کمیته‌ی ریسک بانک» طبق ارزیابی Opus، که در نسخه‌ی قبلی گزارش وجود نداشت.
۲. تعمیق بخش اعتبارات اسنادی با زاویه‌ی تمرکز مشتری — چون این بخش با ~۴٪ پرتفوی، ~۴۰٪ کل مطالبات
   غیرجاری بانک را تشکیل می‌دهد (یافته‌ی محوری بازبینی Opus)، باید مشخص شود این ریسک در دست چند مشتری
   متمرکز است یا پخش.

⚠️ محدودیت روش‌شناختی مشترک هر دو تحلیل: «مشتری» اینجا bر مبنای main_customer_id در
Loan_Contract_Info (گیرنده‌ی اصلی رسمی) تعریف شده، نه Loan_Remain.customer_id (که شامل همه‌ی طرفین
از جمله ضامن‌هاست — طبق یافته‌ی بخش پ). چون ۲۲.۴٪ مانده‌ی تسهیلات اصلاً رکورد Loan_Contract_Info ندارد
(یافته‌ی «orphan»، بخش ت)، این ۲۲.۴٪ در این دو تحلیل قابل انتساب به مشتری نیستند و کنار گذاشته شده‌اند
— یعنی اعداد این صفحه یک کفِ محافظه‌کارانه‌اند، نه تصویر کامل تمرکز واقعی.

خروجی: PNG در reports/figures/phase1_market_overview/ و CSV در data/processed/phase1_market_overview/
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

LATEST_LOAN_TD = 14041229
TOTAL_PORTFOLIO_BALANCE = 1_281_628_119_052_734  # عدد تأییدشده‌ی اسفند ۱۴۰۴ (چند سند/CSV مستقل)


def save_barh(df: pd.DataFrame, label_col: str, value_col: str, title: str, xlabel: str, filename: str) -> None:
    fig, ax = plt.subplots(figsize=(10, max(4, 0.5 * len(df))))
    y_pos = range(len(df))
    ax.barh(y_pos, df[value_col])
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels([fa(str(t)) for t in df[label_col]], fontsize=10)
    ax.set_xlabel(fa(xlabel))
    ax.set_title(fa(title))
    ax.xaxis.set_major_formatter(lambda v, pos: to_persian_digits(f"{v:,.0f}"))
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / filename, dpi=150)
    plt.close(fig)


def section_1_single_name_concentration(engine) -> None:
    """۱. تمرکز تک‌نامی: مانده و NPL بزرگ‌ترین ۲۰ مشتری تسهیلاتی (بر مبنای main_customer_id، نه ضامن)."""
    query = f"""
        WITH LatestLoanBalance AS (
            SELECT loanfile_id, MAX(Total_Remain) AS balance, MAX(MANDE_JARI) AS mande_jari
            FROM dbo.Loan_Remain
            WHERE Transaction_Date = {LATEST_LOAN_TD}
            GROUP BY loanfile_id
        )
        SELECT
            c.main_customer_id,
            COUNT(DISTINCT lb.loanfile_id) AS loan_count,
            SUM(lb.balance) AS total_exposure,
            SUM(lb.balance - lb.mande_jari) AS npl_exposure
        FROM LatestLoanBalance lb
        JOIN dbo.vw_Loan_Contract_Dedup c ON c.loanfile_id = lb.loanfile_id
        WHERE lb.balance > 0
        GROUP BY c.main_customer_id
        ORDER BY total_exposure DESC
    """
    all_customers = pd.read_sql(query, engine)
    matched_total = all_customers["total_exposure"].sum()
    top20 = all_customers.head(20).copy()
    top20["npl_ratio_pct"] = (top20["npl_exposure"] / top20["total_exposure"] * 100).round(1)
    top20["share_of_matched_pct"] = (top20["total_exposure"] / matched_total * 100).round(2)
    top20["share_of_total_portfolio_pct"] = (top20["total_exposure"] / TOTAL_PORTFOLIO_BALANCE * 100).round(2)
    top20["rank"] = range(1, len(top20) + 1)
    # نکته: شناسه‌ی واقعی مشتری (main_customer_id) در CSV برای استفاده‌ی داخلی کمیته‌ی ریسک حفظ شده؛
    # فقط برچسب نمودار (که ممکن است جدا از فایل داده به‌اشتراک گذاشته شود) عمومی/غیرقابل‌شناسایی است.
    top20["customer_label"] = "مشتری #" + top20["rank"].astype(str)

    top20_share_matched = top20["total_exposure"].sum() / matched_total * 100
    top20_share_portfolio = top20["total_exposure"].sum() / TOTAL_PORTFOLIO_BALANCE * 100
    print("\n=== ۱. تمرکز تک‌نامی — Top ۲۰ مشتری تسهیلاتی بر اساس مانده (main_customer_id، آخرین ماه) ===")
    print(top20[["rank", "loan_count", "total_exposure", "npl_ratio_pct", "share_of_total_portfolio_pct"]].to_string(index=False))
    print(f"→ Top ۲۰ مشتری روی‌هم {top20_share_matched:.1f}٪ از مانده‌ی قابل‌انتساب-به-مشتری و "
          f"{top20_share_portfolio:.1f}٪ از کل پرتفوی تسهیلات بانک را در اختیار دارند.")
    print(f"→ (یادآوری محدودیت: {(1 - matched_total / TOTAL_PORTFOLIO_BALANCE) * 100:.1f}٪ از کل پرتفوی به‌دلیل "
          f"نبود رکورد Loan_Contract_Info قابل‌انتساب به مشتری نیست و در این تحلیل لحاظ نشده.)")

    save_barh(top20.sort_values("total_exposure"), "customer_label", "total_exposure",
               "تمرکز تک‌نامی — مانده‌ی Top ۲۰ مشتری تسهیلاتی (شناسه‌ها به‌دلیل محرمانگی نمایش داده نشدند)",
               "مانده‌ی تسهیلات (ریال)", "single_name_concentration_top20.png")
    top20.to_csv(PROCESSED_DIR / "single_name_concentration_top20.csv", index=False)


def section_2_loc_customer_concentration(engine) -> None:
    """۲. تعمیق اعتبارات اسنادی: تعداد مشتریان درگیر و تمرکز مانده در دست آن‌ها (آخرین ماه)."""
    query = f"""
        WITH LOCLoans AS (
            SELECT loanfile_id,
                   MAX(CASE WHEN LTRIM(RTRIM(REPLACE(ECO_SEC,CHAR(34),''))) = N'اعتباراسنادی' THEN 1 ELSE 0 END) AS is_loc,
                   MAX(Total_Remain) AS bal, MAX(MANDE_JARI) AS mande_jari
            FROM dbo.Loan_Remain
            WHERE Transaction_Date = {LATEST_LOAN_TD}
            GROUP BY loanfile_id
        )
        SELECT c.main_customer_id, COUNT(DISTINCT l.loanfile_id) AS loan_count,
               SUM(l.bal) AS total_exposure, SUM(l.bal - l.mande_jari) AS npl_exposure
        FROM LOCLoans l
        JOIN dbo.vw_Loan_Contract_Dedup c ON c.loanfile_id = l.loanfile_id
        WHERE l.is_loc = 1 AND l.bal > 0
        GROUP BY c.main_customer_id
        ORDER BY total_exposure DESC
    """
    df = pd.read_sql(query, engine)
    total_loc_balance = df["total_exposure"].sum()
    total_loc_npl = df["npl_exposure"].sum()
    top10 = df.head(10).copy()
    top10["rank"] = range(1, len(top10) + 1)
    top10["customer_label"] = "مشتری #" + top10["rank"].astype(str)
    top10["npl_ratio_pct"] = (top10["npl_exposure"] / top10["total_exposure"] * 100).round(1)
    top10_share = top10["total_exposure"].sum() / total_loc_balance * 100

    print(f"\n=== ۲. تعمیق اعتبارات اسنادی — {len(df)} مشتری منحصربه‌فرد (قابل‌انتساب) درگیر این بخش‌اند ===")
    print(top10[["rank", "loan_count", "total_exposure", "npl_ratio_pct"]].to_string(index=False))
    print(f"→ Top ۱۰ مشتری {top10_share:.1f}٪ از کل مانده‌ی اعتبارات اسنادی (قابل‌انتساب) را در اختیار دارند "
          f"(از میان {len(df)} مشتری) — {'تمرکز بسیار بالا' if top10_share > 50 else 'تمرکز متوسط'}.")
    print(f"→ نسبت NPL کل بخش اعتبارات اسنادی (قابل‌انتساب): {total_loc_npl / total_loc_balance * 100:.1f}٪")

    save_barh(top10.sort_values("total_exposure"), "customer_label", "total_exposure",
               "تمرکز مشتری در بخش اعتبارات اسنادی — Top ۱۰ مشتری",
               "مانده‌ی اعتبارات اسنادی (ریال)", "loc_customer_concentration_top10.png")
    top10.to_csv(PROCESSED_DIR / "loc_customer_concentration_top10.csv", index=False)
    pd.DataFrame([{"distinct_customers": len(df), "total_loc_balance": total_loc_balance,
                    "total_loc_npl": total_loc_npl, "top10_share_pct": top10_share}]
                 ).to_csv(PROCESSED_DIR / "loc_customer_concentration_summary.csv", index=False)


def main() -> None:
    engine = get_engine()
    section_1_single_name_concentration(engine)
    section_2_loc_customer_concentration(engine)
    print(f"\nخروجی‌ها در {PROCESSED_DIR} و {FIGURES_DIR} ذخیره شدند.")


if __name__ == "__main__":
    main()
