"""
فاز ۱ — بخش سپرده‌گذاران: نمای کلی پرتفوی سپرده و جمعیت سپرده‌گذاران فعال.

⚠️ DRAFT — این اسکریپت در نشست Cowork نوشته شده و اجرا/اعتبارسنجی نشده (این نشست به
SQL Server دسترسی شبکه‌ای ندارد). لطفاً در نشست Claude Code بومی (با دسترسی مستقیم DB) اجرا کنید؛
اگر نتایج غیرمنتظره بود یا خطا داد، نتیجه/خطا را برای اصلاح برگردانید.

پیش‌نیاز: vw_Active_Depositor_Flags باید قبلاً روی Alzahra_Final_DB دیپلوی و Sanity-Check شده باشد
(sql/views/vw_Active_Depositor_Flags.sql) — طبق همان الگوی ۹ View قبلی در docs/06_phase1_sql_views.md.

خروجی:
- reports/figures/phase1_market_overview/deposit_portfolio_composition.png
- reports/figures/phase1_market_overview/deposit_balance_trend.png
- data/processed/phase1_market_overview/depositors_summary.csv
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

LATEST_MONTH = 140412  # اسفند ۱۴۰۴ — طبق docs/03_data_dictionary.md؛ اگر داده به‌روز شد اصلاح شود


def main() -> None:
    engine = get_engine()

    # ۱. ترکیب پرتفوی سپرده در آخرین ماه موجود، به تفکیک نوع سپرده
    # ⚠️ رفع (بازبینی مستقل Claude Opus، ۲۰۲۶-۰۹-۱۱، بند ۲.۹): نسخه‌ی اول بر اساس avg_balance (میانگین
    # هر حساب) مرتب/رسم می‌شد که سطل «نامشخص» را در جایی گمنام دفن می‌کرد. «نامشخص» در واقع از نظر تعداد
    # حساب بزرگ‌ترین سطل است (۸۴۸,۵۵۳ حساب، ~۴۰٪ کل) و ۱۱.۸٪ مانده‌ی کل را هم دارد — ناشی از ۳۷٪ ردیف
    # Deposit_Monthly_Activity که deposit_id آن‌ها در Deposit_Accoutnt_Info نیست (طبق تعریف خودِ View).
    # نمودار حالا بر اساس مانده‌ی کل (account_count × avg_balance) مرتب می‌شود و سطل نامشخص رنگ/برچسب
    # جداگانه دارد تا دیده نشدنش در نسخه‌ی قبلی تکرار نشود.
    portfolio = pd.read_sql(
        f"""
        SELECT deposit_type, account_count, avg_balance
        FROM dbo.vw_Deposit_Portfolio_Monthly
        WHERE year_mount = {LATEST_MONTH}
        ORDER BY avg_balance DESC
        """,
        engine,
    )
    portfolio["total_balance"] = portfolio["account_count"] * portfolio["avg_balance"]
    portfolio["account_share_pct"] = (portfolio["account_count"] / portfolio["account_count"].sum() * 100).round(1)
    portfolio["balance_share_pct"] = (portfolio["total_balance"] / portfolio["total_balance"].sum() * 100).round(1)
    print("=== ترکیب پرتفوی سپرده (آخرین ماه) ===")
    print(portfolio.to_string(index=False))
    unknown_row = portfolio[portfolio["deposit_type"] == "نامشخص"]
    if not unknown_row.empty:
        print(f"→ سطل «نامشخص» {unknown_row['account_share_pct'].iloc[0]:.1f}٪ کل حساب‌ها و "
              f"{unknown_row['balance_share_pct'].iloc[0]:.1f}٪ کل مانده را دارد — ناشی از عدم تطابق "
              f"deposit_id با Deposit_Accoutnt_Info (محدودیت مستندشده‌ی View، نه خطای این اسکریپت).")

    if not portfolio.empty:
        portfolio_by_balance = portfolio.sort_values("total_balance", ascending=True)
        colors = ["tab:red" if t == "نامشخص" else "tab:blue" for t in portfolio_by_balance["deposit_type"]]
        fig, ax = plt.subplots(figsize=(10, 6))
        y_pos = range(len(portfolio_by_balance))
        ax.barh(y_pos, portfolio_by_balance["total_balance"], color=colors)
        ax.set_yticks(list(y_pos))
        ax.set_yticklabels([fa(t) for t in portfolio_by_balance["deposit_type"]], fontsize=10)
        ax.set_xlabel(fa("مانده کل (ریال)"))
        ax.set_title(f'{fa("ترکیب پرتفوی سپرده به تفکیک نوع — ماه")} {to_persian_digits(LATEST_MONTH)}\n'
                     f'{fa("(رنگ قرمز = نامشخص، به‌دلیل عدم تطابق شناسه با Deposit_Accoutnt_Info)")}')
        ax.xaxis.set_major_formatter(lambda v, pos: to_persian_digits(f"{v:,.0f}"))
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / "deposit_portfolio_composition.png", dpi=150)
        plt.close(fig)

    # ۲. روند مانده‌ی کل سپرده طی کل دوره (۷۱ ماهه)
    trend = pd.read_sql(
        """
        SELECT year_mount, SUM(account_count * avg_balance) AS total_balance_estimate,
               SUM(account_count) AS total_accounts
        FROM dbo.vw_Deposit_Portfolio_Monthly
        GROUP BY year_mount
        ORDER BY year_mount
        """,
        engine,
    )
    print("\n=== روند مانده‌ی کل سپرده (نمونه‌ی ۵ ماه اول/آخر) ===")
    print(pd.concat([trend.head(), trend.tail()]).to_string(index=False))

    if not trend.empty:
        fig, ax = plt.subplots(figsize=(12, 5))
        x_pos = range(len(trend))
        x_labels = [to_persian_digits(v) for v in trend["year_mount"].astype(int).astype(str)]
        ax.plot(list(x_pos), trend["total_balance_estimate"])
        ax.set_xticks(list(x_pos))
        ax.set_xticklabels(x_labels, rotation=90, fontsize=6)
        ax.set_title(fa("روند مانده‌ی تخمینی کل سپرده در طول زمان"))
        ax.set_xlabel(fa("ماه (شمسی YYYYMM)"))
        ax.set_ylabel(fa("مانده‌ی تخمینی کل (ریال)"))
        ax.yaxis.set_major_formatter(lambda v, pos: to_persian_digits(f"{v:,.0f}"))
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / "deposit_balance_trend.png", dpi=150)
        plt.close(fig)

    # ۳. جمعیت سپرده‌گذاران فعال در برابر کل (نیازمند vw_Active_Depositor_Flags — بخش ۳ لیست کارها)
    try:
        active_summary = pd.read_sql(
            """
            SELECT
                COUNT(*)                                    AS total_depositors,
                SUM(is_active_depositor)                    AS active_depositors,
                CAST(SUM(is_active_depositor) AS FLOAT) / COUNT(*) AS active_share
            FROM dbo.vw_Active_Depositor_Flags
            """,
            engine,
        )
        print("\n=== جمعیت سپرده‌گذاران فعال (سرشماری کامل، نه نمونه) ===")
        print(active_summary.to_string(index=False))
        print(
            "\nمقایسه با گزارش نمونه‌گیری (docs/07_sampling_methodology.md، بخش ۳): "
            "۱,۶۲۵,۲۶۲ حقیقی + ۵۸,۵۱۳ حقوقی فعال (سناریوی محافظه‌کارانه)."
        )
        active_summary.to_csv(PROCESSED_DIR / "depositors_active_summary.csv", index=False)
    except Exception as exc:  # noqa: BLE001 — این بخش وابسته به View آزمایش‌نشده است
        print(f"\n⚠️ خطا در خواندن vw_Active_Depositor_Flags (احتمالاً هنوز دیپلوی نشده): {exc}")

    portfolio.to_csv(PROCESSED_DIR / "deposit_portfolio_latest_month.csv", index=False)
    trend.to_csv(PROCESSED_DIR / "deposit_balance_trend_full.csv", index=False)
    print(f"\nخروجی‌ها در {PROCESSED_DIR} و {FIGURES_DIR} ذخیره شدند.")


if __name__ == "__main__":
    main()
