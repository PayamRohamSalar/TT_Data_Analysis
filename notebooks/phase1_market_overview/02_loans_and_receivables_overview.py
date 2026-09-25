"""
فاز ۱ — بخش تسهیلات‌گیرندگان و مطالبات بانکی: مانده تسهیلات، طبقه‌بندی مطالبات (جاری/غیرجاری)،
و جمعیت تسهیلات‌گیرندگان فعال.

⚠️ DRAFT — نوشته‌شده در نشست Cowork، اجرا/اعتبارسنجی نشده (بدون دسترسی شبکه‌ای به SQL Server از این
نشست). در Claude Code بومی اجرا کنید و نتیجه/خطا را برگردانید.

پیش‌نیاز: vw_Active_Loan_Customer_Flags باید دیپلوی و Sanity-Check شده باشد
(sql/views/vw_Active_Loan_Customer_Flags.sql).

⚠️ محدودیت شناخته‌شده (docs/06_phase1_sql_views.md، بند ۵): vw_Loan_Remain_By_Branch_Month فقط ۸۹.۴٪ از
ارزش مانده‌ی تسهیلات را به شعبه وصل می‌کند؛ ۱۰.۶٪ باقی‌مانده در این View با branch_code=NULL می‌آید ولی
در SUM های سطح کل (بدون GROUP BY شعبه) کامل لحاظ می‌شود — پس اعداد کل این اسکریپت درست‌اند، فقط تفکیک شعبه‌ای ناقص است.

خروجی:
- reports/figures/phase1_market_overview/receivables_classification_trend.png
- reports/figures/phase1_market_overview/receivables_by_sector_latest.png
- data/processed/phase1_market_overview/loans_receivables_summary.csv
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

LATEST_MONTH = 140412  # اسفند ۱۴۰۴


def main() -> None:
    engine = get_engine()

    # ۱. روند ماهانه‌ی طبقه‌بندی مطالبات (جاری / سررسیدگذشته / معوق / مشکوک) — کل بانک
    trend = pd.read_sql(
        """
        SELECT
            year_month,
            SUM(current_balance)    AS current_balance,
            SUM(overusance_balance) AS overusance_balance,
            SUM(postponed_balance)  AS postponed_balance,
            SUM(doubtful_balance)   AS doubtful_balance,
            SUM(total_balance)      AS total_balance
        FROM dbo.vw_Loan_Remain_By_Branch_Month
        GROUP BY year_month
        ORDER BY year_month
        """,
        engine,
    )
    print("=== روند طبقه‌بندی مطالبات (نمونه ۵ ماه اول/آخر) ===")
    print(pd.concat([trend.head(), trend.tail()]).to_string(index=False))

    if not trend.empty:
        fig, ax = plt.subplots(figsize=(12, 6))
        x_pos = range(len(trend))
        x_labels = [to_persian_digits(v) for v in trend["year_month"].astype(int).astype(str)]
        ax.stackplot(
            list(x_pos),
            trend["current_balance"],
            trend["overusance_balance"],
            trend["postponed_balance"],
            trend["doubtful_balance"],
            labels=[fa("جاری"), fa("سررسیدگذشته"), fa("معوق"), fa("مشکوک‌الوصول")],
        )
        ax.set_xticks(list(x_pos))
        ax.set_xticklabels(x_labels, rotation=90, fontsize=6)
        ax.set_title(fa("روند طبقه‌بندی مطالبات تسهیلات (کل بانک)"))
        ax.set_xlabel(fa("ماه (شمسی YYYYMM)"))
        ax.set_ylabel(fa("مانده (ریال)"))
        ax.yaxis.set_major_formatter(lambda v, pos: to_persian_digits(f"{v:,.0f}"))
        ax.legend(loc="upper left", prop={"family": "Vazirmatn"})
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / "receivables_classification_trend.png", dpi=150)
        plt.close(fig)

    # ۲. ترکیب مطالبات به تفکیک بخش اقتصادی در آخرین ماه
    by_sector = pd.read_sql(
        f"""
        SELECT economic_sector,
               SUM(total_balance)    AS total_balance,
               SUM(total_npl_balance) AS npl_balance,
               SUM(loan_count)        AS loan_count
        FROM dbo.vw_Loan_Remain_By_Branch_Month
        WHERE year_month = {LATEST_MONTH} AND economic_sector IS NOT NULL
        GROUP BY economic_sector
        ORDER BY total_balance DESC
        """,
        engine,
    )
    print("\n=== ترکیب مطالبات به تفکیک بخش اقتصادی (آخرین ماه) ===")
    print(by_sector.to_string(index=False))

    if not by_sector.empty:
        fig, ax = plt.subplots(figsize=(10, 6))
        y_pos = range(len(by_sector))
        ax.barh(y_pos, by_sector["total_balance"])
        ax.set_yticks(list(y_pos))
        ax.set_yticklabels([fa(t) for t in by_sector["economic_sector"]], fontsize=10)
        ax.set_xlabel(fa("مانده کل (ریال)"))
        ax.set_title(f'{fa("مانده تسهیلات به تفکیک بخش اقتصادی — ماه")} {to_persian_digits(LATEST_MONTH)}')
        ax.xaxis.set_major_formatter(lambda v, pos: to_persian_digits(f"{v:,.0f}"))
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / "receivables_by_sector_latest.png", dpi=150)
        plt.close(fig)

    # ۳. جمعیت تسهیلات‌گیرندگان فعال (نیازمند vw_Active_Loan_Customer_Flags)
    try:
        active_summary = pd.read_sql(
            """
            SELECT
                COUNT(*)                              AS total_loan_customers,
                SUM(is_active_loan_customer)          AS active_loan_customers,
                CAST(SUM(is_active_loan_customer) AS FLOAT) / COUNT(*) AS active_share
            FROM dbo.vw_Active_Loan_Customer_Flags
            """,
            engine,
        )
        print("\n=== جمعیت تسهیلات‌گیرندگان فعال (سرشماری کامل، نه نمونه) ===")
        print(active_summary.to_string(index=False))
        print(
            "\nمقایسه با گزارش نمونه‌گیری (docs/07_sampling_methodology.md، بخش ۳): "
            "۱,۵۵۵,۸۳۳ حقیقی + ۲۷,۳۳۵ حقوقی فعال."
        )
        active_summary.to_csv(PROCESSED_DIR / "loan_customers_active_summary.csv", index=False)
    except Exception as exc:  # noqa: BLE001
        print(f"\n⚠️ خطا در خواندن vw_Active_Loan_Customer_Flags (احتمالاً هنوز دیپلوی نشده): {exc}")

    trend.to_csv(PROCESSED_DIR / "receivables_classification_trend_full.csv", index=False)
    by_sector.to_csv(PROCESSED_DIR / "receivables_by_sector_latest_month.csv", index=False)
    print(f"\nخروجی‌ها در {PROCESSED_DIR} و {FIGURES_DIR} ذخیره شدند.")


if __name__ == "__main__":
    main()
