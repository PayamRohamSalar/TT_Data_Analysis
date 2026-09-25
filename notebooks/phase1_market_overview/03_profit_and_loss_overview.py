"""
فاز ۱ — بخش سود و زیان: برآورد تقریبی سود/زیان ماهانه از ترکیب سود دریافتی تسهیلات، هزینه سود سپرده،
و درآمد کارمزد.

⚠️ DRAFT — نوشته‌شده در نشست Cowork، اجرا/اعتبارسنجی نشده. در Claude Code بومی اجرا کنید.

⚠️ محدودیت مهم (docs/06_phase1_sql_views.md، بند ۶): هزینه‌ی سود سپرده (vw_Deposit_Interest_Cost_Monthly)
عددی با عدم‌قطعیت ذاتی داده است — سه روش محاسبه سه عدد متفاوت می‌دهند (خام / DISTINCT / جدول مرجع بانک،
بازه‌ی ۵.۱ تا ۱۴.۶ هزار میلیارد ریال برای اسفند ۱۴۰۴). این اسکریپت از نسخه‌ی DISTINCT-شده (View فعلی)
استفاده می‌کند اما نتیجه‌ی سود/زیان باید در گزارش نهایی «با بازه‌ی عدم‌قطعیت» ارائه شود، نه عدد قطعی.
هیچ داده‌ی صریح P&L در دیتابیس وجود ندارد (docs/03_data_dictionary.md) — این برآورد جایگزین دفتر مالی رسمی نیست.

خروجی:
- reports/figures/phase1_market_overview/profit_and_loss_estimate_trend.png
- data/processed/phase1_market_overview/profit_and_loss_estimate.csv
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


def main() -> None:
    engine = get_engine()

    loan_income = pd.read_sql(
        """
        SELECT year_month, SUM(total_interest_paid) AS loan_interest_income,
               SUM(total_penalty_paid) AS loan_penalty_income
        FROM dbo.vw_Loan_Interest_Income_Monthly
        GROUP BY year_month
        """,
        engine,
    )

    deposit_cost = pd.read_sql(
        """
        SELECT year_month, SUM(total_interest_paid) AS deposit_interest_cost
        FROM dbo.vw_Deposit_Interest_Cost_Monthly
        GROUP BY year_month
        """,
        engine,
    )

    fee_income = pd.read_sql(
        """
        SELECT year_mount AS year_month, SUM(total_amount) AS fee_income
        FROM dbo.vw_Fee_Income_Monthly
        GROUP BY year_mount
        """,
        engine,
    )

    merged = (
        loan_income.merge(deposit_cost, on="year_month", how="outer")
        .merge(fee_income, on="year_month", how="outer")
        .fillna(0)
        .sort_values("year_month")
    )

    # نکته‌ی منطقی (نه سینتکسی) که در اجرای واقعی کشف شد: جداول هزینه‌ی سود سپرده و کارمزد فقط تا ۱۴۰۴/۱۲
    # داده دارند (شرح کامل در docs/08_data_landscape_report.md، بخش «شکاف ۳ماهه»)، در حالی‌که
    # Loan_Monthly_Activity.payed_date تا ۱۴۰۵/۰۳ می‌رود. بدون این فیلتر، ماه‌های ۱۴۰۵/۰۱ تا ۱۴۰۵/۰۳ فقط
    # نیمی از اجزای سود/زیان را دارند (صرفاً سود تسهیلات، بدون هزینه‌ی سپرده/کارمزد) و net_estimate برای
    # آن‌ها به‌طور مصنوعی و گمراه‌کننده بزرگ می‌شود. این ماه‌های ناقص را از گزارش نهایی حذف می‌کنیم.
    LAST_COMPLETE_MONTH = 140412
    incomplete_months = sorted(merged.loc[merged["year_month"] > LAST_COMPLETE_MONTH, "year_month"].tolist())
    if incomplete_months:
        print(
            f"\n⚠️ ماه‌های {incomplete_months} از گزارش حذف شدند — داده‌ی هزینه‌ی سود سپرده و کارمزد "
            f"فقط تا {LAST_COMPLETE_MONTH} تکمیل شده است (شکاف ۳ماهه، رجوع به docs/08_data_landscape_report.md)."
        )
    merged = merged.loc[merged["year_month"] <= LAST_COMPLETE_MONTH].copy()

    merged["net_estimate"] = (
        merged["loan_interest_income"]
        + merged["loan_penalty_income"]
        + merged["fee_income"]
        - merged["deposit_interest_cost"]
    )

    print("=== برآورد سود/زیان ماهانه (نمونه ۵ ماه اول/آخر) ===")
    print(pd.concat([merged.head(), merged.tail()]).to_string(index=False))
    print(
        "\n⚠️ ستون deposit_interest_cost دارای عدم‌قطعیت ذاتی داده است "
        "(بازه‌ی واقعی می‌تواند تا ~۳ برابر مقدار این ستون هم برسد — رجوع به بند ۶ در docs/06_phase1_sql_views.md)."
    )

    if not merged.empty:
        fig, ax = plt.subplots(figsize=(12, 6))
        x_pos = range(len(merged))
        x_labels = [to_persian_digits(v) for v in merged["year_month"].astype(int).astype(str)]
        # ⚠️ رفع (بازبینی مستقل Claude Opus، ۲۰۲۶-۰۹-۱۱، بند ۲.۳ و ۲.۱۱):
        # (۱) محور y به «هزار میلیارد ریال» مقیاس شد (قبلاً ریال خام با ۱۳ رقم، غیرقابل‌خواندن بود).
        # (۲) برچسب «برآورد خالص» به «حاشیه‌ی ناخالص مالی برآوردی» تغییر کرد — چون این عدد هیچ‌کدام از
        # هزینه‌ی اداری/پرسنلی، ذخیره‌ی مطالبات مشکوک‌الوصول، سایر درآمد/هزینه، یا مالیات را ندارد؛ عنوان
        # «سود خالص» گمراه‌کننده بود.
        SCALE = 1e12  # ریال -> هزار میلیارد ریال
        ax.plot(list(x_pos), (merged["loan_interest_income"] + merged["loan_penalty_income"]) / SCALE, label=fa("درآمد سود+جریمه تسهیلات"))
        ax.plot(list(x_pos), merged["fee_income"] / SCALE, label=fa("درآمد کارمزد"))
        ax.plot(list(x_pos), -merged["deposit_interest_cost"] / SCALE, label=fa("هزینه سود سپرده (منفی)"))
        ax.plot(list(x_pos), merged["net_estimate"] / SCALE, label=fa("حاشیه‌ی ناخالص مالی برآوردی"), linewidth=2, linestyle="--")
        ax.set_xticks(list(x_pos))
        ax.set_xticklabels(x_labels, rotation=90, fontsize=6)
        ax.set_title(fa("برآورد تقریبی حاشیه‌ی ناخالص مالی ماهانه (با عدم‌قطعیت در هزینه سود سپرده؛ بدون هزینه‌ی اداری/ذخیره/مالیات)"))
        ax.set_xlabel(fa("ماه (شمسی YYYYMM)"))
        ax.set_ylabel(fa("هزار میلیارد ریال"))
        ax.yaxis.set_major_formatter(lambda v, pos: to_persian_digits(f"{v:,.1f}"))
        ax.legend(prop={"family": "Vazirmatn"})
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / "profit_and_loss_estimate_trend.png", dpi=150)
        plt.close(fig)

    merged.to_csv(PROCESSED_DIR / "profit_and_loss_estimate.csv", index=False)
    print(f"\nخروجی‌ها در {PROCESSED_DIR} و {FIGURES_DIR} ذخیره شدند.")


if __name__ == "__main__":
    main()
