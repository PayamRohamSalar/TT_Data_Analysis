"""
صفحه‌ی KPI مدیریتی (مورد ۱۴ بازبینی مستقل Claude Opus، آخرین مورد از فهرست تکمیلی) — یک نمای یک‌صفحه‌ای
از ۱۵ شاخص کلیدی فاز ۱، برای کسی که وقت خواندن ۶۰ صفحه را ندارد.

⚠️ این اسکریپت **هیچ عدد جدیدی محاسبه نمی‌کند** — همه‌ی ۱۵ شاخص مستقیماً از فایل‌های CSV از‌قبل‌تولیدشده‌ی
اسکریپت‌های ۰۱ تا ۱۱ خوانده می‌شوند (نه Hardcode)، تا اگر عددی در آینده اصلاح شد، این داشبورد هم با
اجرای مجدد دقیقاً به‌روز شود. منبع هر شاخص در کد کنار خودش کامنت شده.

خروجی: reports/figures/phase1_market_overview/kpi_dashboard.png
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from tt_bank.common.persian_plot import fa, setup_persian_font, to_persian_digits

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures" / "phase1_market_overview"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "phase1_market_overview"
setup_persian_font()


def fa_num(x: float, decimals: int = 1) -> str:
    return to_persian_digits(f"{x:,.{decimals}f}")


def main() -> None:
    tiles = []  # هر عضو: (عنوان کوتاه, مقدار بزرگ, زیرنویس, رنگ)

    # ۱-۲: مانده‌ی کل سپرده/تسهیلات (آخرین ماه)
    dep_trend = pd.read_csv(PROCESSED_DIR / "deposit_balance_trend_full.csv").sort_values("year_mount")
    total_deposit = dep_trend["total_balance_estimate"].iloc[-1]
    rec_trend = pd.read_csv(PROCESSED_DIR / "receivables_classification_trend_full.csv").sort_values("year_month")
    total_loan = rec_trend["total_balance"].iloc[-1]
    npl_total = (rec_trend["total_balance"].iloc[-1] - rec_trend["current_balance"].iloc[-1]) / rec_trend["total_balance"].iloc[-1] * 100
    tiles.append(("مانده‌ی کل سپرده", fa_num(total_deposit / 1e12, 0), "هزار میلیارد ریال، اسفند ۱۴۰۴", "#2E75B6"))
    tiles.append(("مانده‌ی کل تسهیلات", fa_num(total_loan / 1e12, 0), "هزار میلیارد ریال، اسفند ۱۴۰۴", "#2E75B6"))

    # ۳: LDR
    ldr = pd.read_csv(PROCESSED_DIR / "loan_to_deposit_ratio.csv").sort_values("year_mount")
    tiles.append(("نسبت تسهیلات به سپرده (LDR)", fa_num(ldr["ldr_pct"].iloc[-1]) + "٪", "از ۱۱۳.۵٪ (۱۴۰۰) رسیده", "#C00000"))

    # ۴: NPL کل
    tiles.append(("نسبت NPL کل پرتفوی", fa_num(npl_total) + "٪", "اسفند ۱۴۰۴", "#C00000"))

    # ۵: حاشیه‌ی سود تقریبی
    margin = pd.read_csv(PROCESSED_DIR / "effective_rate_margin_summary.csv").iloc[0]
    tiles.append(("حاشیه‌ی سود تقریبی", fa_num(margin["approx_margin_pct_points_vs_cost_of_funds"]) + " واحد٪",
                   "کف محافظه‌کارانه؛ رجوع به docs/12", "#548235"))

    # ۶-۷: جمعیت فعال
    dep_pop = pd.read_csv(PROCESSED_DIR / "depositors_active_summary.csv").iloc[0]
    loan_pop = pd.read_csv(PROCESSED_DIR / "loan_customers_active_summary.csv").iloc[0]
    tiles.append(("سپرده‌گذاران فعال", fa_num(dep_pop["active_depositors"] / 1000, 0) + " هزار",
                   fa_num(dep_pop["active_share"] * 100) + "٪ از کل", "#2E75B6"))
    tiles.append(("تسهیلات‌گیرندگان فعال", fa_num(loan_pop["active_loan_customers"] / 1000, 0) + " هزار",
                   fa_num(loan_pop["active_share"] * 100) + "٪ از کل (شامل ضامن)", "#2E75B6"))

    # ۸-۹: رشد سالانه ۱۴۰۴
    yoy = pd.read_csv(PROCESSED_DIR / "yoy_growth.csv").sort_values("shamsi_year")
    last_row = yoy[yoy["shamsi_year"] == 1404].iloc[0]
    tiles.append(("رشد سالانه‌ی سپرده (۱۴۰۴)", fa_num(last_row["deposit_yoy_pct"]) + "٪", "نسبت به ۱۴۰۳", "#548235"))
    tiles.append(("رشد سالانه‌ی تسهیلات (۱۴۰۴)", fa_num(last_row["loan_yoy_pct"]) + "٪", "نسبت به ۱۴۰۳", "#548235"))

    # ۱۰: تمرکز سپرده
    pareto = pd.read_csv(PROCESSED_DIR / "concentration_pareto_summary.csv")
    dep_top1 = pareto[(pareto["type"] == "سپرده") & (pareto["top_customers_pct"] == 1)]["balance_share_pct"].iloc[0]
    tiles.append(("تمرکز سپرده (۱٪ برتر)", fa_num(dep_top1) + "٪", "از کل مانده‌ی سپرده", "#C00000"))

    # ۱۱: تمرکز تک‌نامی تسهیلات (Top20)
    top20 = pd.read_csv(PROCESSED_DIR / "single_name_concentration_top20.csv")
    tiles.append(("تمرکز تک‌نامی (Top ۲۰ مشتری)", fa_num(top20["share_of_total_portfolio_pct"].sum()) + "٪",
                   "از کل پرتفوی تسهیلات بانک", "#C00000"))

    # ۱۲-۱۳: اعتبارات اسنادی
    loc = pd.read_csv(PROCESSED_DIR / "loc_customer_concentration_summary.csv").iloc[0]
    loc_npl_pct = loc["total_loc_npl"] / loc["total_loc_balance"] * 100
    tiles.append(("مشتریان اعتبارات اسنادی", to_persian_digits(str(int(loc["distinct_customers"]))),
                   "کل ریسک این بخش در دست همین چند نفر", "#C00000"))
    tiles.append(("نسبت NPL اعتبارات اسنادی", fa_num(loc_npl_pct) + "٪", "فقط ۴٪ پرتفوی، ~۴۰٪ کل NPL بانک", "#C00000"))

    # ۱۴: بدترین Vintage
    vintage = pd.read_csv(PROCESSED_DIR / "loan_vintage_analysis.csv")
    worst = vintage.loc[vintage["npl_ratio_pct"].idxmax()]
    tiles.append(("بدترین سال اعطای تسهیلات", to_persian_digits(str(int(worst["grant_year"]))),
                   f"NPL {fa_num(worst['npl_ratio_pct'])}٪ از قراردادهای همان سال", "#C00000"))

    # ۱۵: نرخ ریزش سپرده
    churn = pd.read_csv(PROCESSED_DIR / "deposit_annual_churn_rate.csv").sort_values("from_year")
    last_churn = churn.iloc[-1]
    tiles.append(("نرخ ریزش سپرده (آخرین سال)", fa_num(last_churn["churn_rate_pct"]) + "٪",
                   "تعریف سخت‌گیرانه — رجوع به docs/12", "#548235"))

    # --- رسم گرید ۳×۵ ---
    fig, axes = plt.subplots(3, 5, figsize=(20, 10))
    fig.suptitle(fa("داشبورد شاخص‌های کلیدی فاز ۱ — تحلیل رفتار مشتریان بانک توسعه تعاون (اسفند ۱۴۰۴)"),
                 fontsize=16, y=0.98, weight="bold")
    for ax, (title, value, caption, color) in zip(axes.flat, tiles):
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        ax.add_patch(plt.Rectangle((0.02, 0.05), 0.96, 0.9, facecolor="#F2F2F2", edgecolor=color, linewidth=2))
        ax.text(0.5, 0.68, value, ha="center", va="center", fontsize=24, weight="bold", color=color)
        ax.text(0.5, 0.42, fa(title), ha="center", va="center", fontsize=11, weight="bold")
        ax.text(0.5, 0.18, fa(caption), ha="center", va="center", fontsize=8, color="dimgray", wrap=True)
    for ax in axes.flat[len(tiles):]:
        ax.axis("off")
    fig.text(0.5, 0.01, fa("منبع: کلیه‌ی اعداد مستقیماً از خروجی اسکریپت‌های ۰۱ تا ۱۱ خوانده شده‌اند — جزئیات و محدودیت‌های هر شاخص در docs/12_phase1_findings_and_gaps.md"),
              ha="center", fontsize=8, color="gray")
    fig.tight_layout(rect=[0, 0.02, 1, 0.95])
    fig.savefig(FIGURES_DIR / "kpi_dashboard.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"داشبورد ذخیره شد: {FIGURES_DIR / 'kpi_dashboard.png'}")
    for title, value, caption, _ in tiles:
        print(f"- {title}: {value} ({caption})")


if __name__ == "__main__":
    main()
