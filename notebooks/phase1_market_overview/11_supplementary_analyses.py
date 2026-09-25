"""
تحلیل‌های تکمیلی پیشنهادشده در بازبینی مستقل Claude Opus (۲۰۲۶-۰۹-۱۱، بند ۳.ب، موارد ۸/۹/۱۰/۱۲/۱۴)،
به تأیید کاربر، به‌صورت مرحله‌به‌مرحله ساخته می‌شود — این فایل هر نشست با یک بخش جدید رشد می‌کند.

۸. پلکان مانده‌ی سپرده — توزیع مشتریان و مانده در بازه‌های مانده (ساختار بازار سپرده)
۹. پروفایل سررسید تسهیلات — مانده به تفکیک عمر باقی‌مانده‌ی قرارداد (برای مدیریت نقدینگی/ALM)
۱۰. NPL به تفکیک اندازه‌ی وام و اندازه‌ی شعبه
۱۲. نرخ ریزش سالانه‌ی سپرده‌گذاران (Churn) — نه فقط ماندگاری کوهورت، بلکه گذار سال‌به‌سال
[مورد ۱۴ در نشست بعدی اضافه می‌شود]

خروجی: PNG در reports/figures/phase1_market_overview/ و CSV در data/processed/phase1_market_overview/
"""

from pathlib import Path

import jdatetime
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


def jalali_str_to_ordinal(s: str):
    """رشته‌ی 'YYYY/MM/DD' شمسی را به عدد ترتیبی میلادی (ordinal) تبدیل می‌کند؛ نامعتبر -> None."""
    try:
        y, m, d = (int(p) for p in s.split("/"))
        return jdatetime.date(y, m, d).togregorian().toordinal()
    except (ValueError, TypeError):
        return None

LATEST_MONTH = 140412
LATEST_LOAN_TD = 14041229


def section_8_deposit_balance_ladder(engine) -> None:
    """۸. پلکان مانده‌ی سپرده — توزیع مشتریان (و سهم مانده) در بازه‌های مانده‌ی کل، آخرین ماه."""
    query = f"""
        WITH CustomerBalance AS (
            SELECT customer_id, SUM(avr_total_amount_eq) AS total_balance
            FROM dbo.Deposit_Monthly_Activity
            WHERE year_mount = {LATEST_MONTH}
            GROUP BY customer_id
            HAVING SUM(avr_total_amount_eq) > 0
        )
        SELECT
            CASE
                WHEN total_balance < 5000000        THEN N'۱) زیر ۵ میلیون'
                WHEN total_balance < 25000000       THEN N'۲) ۵ تا ۲۵ میلیون'
                WHEN total_balance < 100000000      THEN N'۳) ۲۵ تا ۱۰۰ میلیون'
                WHEN total_balance < 500000000      THEN N'۴) ۱۰۰ تا ۵۰۰ میلیون'
                WHEN total_balance < 2000000000     THEN N'۵) ۵۰۰م تا ۲ میلیارد'
                WHEN total_balance < 10000000000    THEN N'۶) ۲ تا ۱۰ میلیارد'
                ELSE                                      N'۷) بالای ۱۰ میلیارد'
            END AS balance_tier,
            COUNT(*) AS customer_count,
            SUM(total_balance) AS tier_total_balance
        FROM CustomerBalance
        GROUP BY
            CASE
                WHEN total_balance < 5000000        THEN N'۱) زیر ۵ میلیون'
                WHEN total_balance < 25000000       THEN N'۲) ۵ تا ۲۵ میلیون'
                WHEN total_balance < 100000000      THEN N'۳) ۲۵ تا ۱۰۰ میلیون'
                WHEN total_balance < 500000000      THEN N'۴) ۱۰۰ تا ۵۰۰ میلیون'
                WHEN total_balance < 2000000000     THEN N'۵) ۵۰۰م تا ۲ میلیارد'
                WHEN total_balance < 10000000000    THEN N'۶) ۲ تا ۱۰ میلیارد'
                ELSE                                      N'۷) بالای ۱۰ میلیارد'
            END
        ORDER BY balance_tier
    """
    df = pd.read_sql(query, engine)
    df["customer_share_pct"] = (df["customer_count"] / df["customer_count"].sum() * 100).round(2)
    df["balance_share_pct"] = (df["tier_total_balance"] / df["tier_total_balance"].sum() * 100).round(2)
    print("\n=== ۸. پلکان مانده‌ی سپرده — توزیع مشتریان و مانده در بازه‌های مانده (آخرین ماه) ===")
    print(df.to_string(index=False))
    mass_tier = df.loc[df["customer_share_pct"].idxmax(), "balance_tier"]
    value_tier = df.loc[df["balance_share_pct"].idxmax(), "balance_tier"]
    print(f"→ بیشترین تعداد مشتری در بازه‌ی «{mass_tier}» است، ولی بیشترین سهم ارزشی مانده در بازه‌ی "
          f"«{value_tier}» — فاصله‌ی این دو، شکل نامتقارن بازار سپرده را نشان می‌دهد.")

    if not df.empty:
        fig, ax1 = plt.subplots(figsize=(11, 6))
        x_pos = range(len(df))
        ax1.bar([p - 0.2 for p in x_pos], df["customer_share_pct"], width=0.4, color="tab:blue", label=fa("سهم تعداد مشتری"))
        ax1.set_ylabel(fa("سهم تعداد مشتری (درصد)"), color="tab:blue")
        ax1.yaxis.set_major_formatter(lambda v, pos: to_persian_digits(f"{v:,.0f}") + "%")
        ax2 = ax1.twinx()
        ax2.bar([p + 0.2 for p in x_pos], df["balance_share_pct"], width=0.4, color="tab:orange", label=fa("سهم مانده"))
        ax2.set_ylabel(fa("سهم مانده‌ی کل (درصد)"), color="tab:orange")
        ax2.yaxis.set_major_formatter(lambda v, pos: to_persian_digits(f"{v:,.0f}") + "%")
        ax1.set_xticks(list(x_pos))
        ax1.set_xticklabels([fa(t) for t in df["balance_tier"]], rotation=25, ha="right", fontsize=8)
        ax1.set_title(fa("پلکان مانده‌ی سپرده: سهم تعداد مشتری در برابر سهم مانده، به تفکیک بازه"))
        fig.legend(loc="upper center", bbox_to_anchor=(0.5, 0.95), ncol=2, prop={"family": "Vazirmatn"})
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / "deposit_balance_ladder.png", dpi=150)
        plt.close(fig)
    df.to_csv(PROCESSED_DIR / "deposit_balance_ladder.csv", index=False)


def section_9_loan_maturity_profile(engine) -> None:
    """۹. پروفایل سررسید تسهیلات — مانده‌ی فعلی به تفکیک عمر باقی‌مانده‌ی قرارداد (سررسید = تاریخ اعطا + DURATION_DAYS).

    ⚠️ محدودیت‌های روش‌شناختی:
    - فقط برای وام‌هایی محاسبه می‌شود که هم در Loan_Contract_Info رکورد دارند (grant_date/duration_days)
      هم در آخرین ماه Loan_Remain مانده‌ی مثبت — یعنی همان ۷۷.۶٪ پرتفوی «شناخته‌شده» (بند ۴ در
      docs/12_phase1_findings_and_gaps.md)، نه کل پرتفوی.
    - ۵۷ ردیف با DURATION_DAYS منفی (باگ محلی محصول «کمک هزینه ودیعه مسکن کارکنان»، بند ۴ همان سند)
      فیلتر شدند.
    - «سررسیدگذشته» به معنای واقعیِ NPL نیست؛ یعنی تاریخ سررسید برنامه‌ریزی‌شده گذشته ولی قرارداد هنوز
      مانده دارد — می‌تواند به‌دلیل تمدید/استمهال هم باشد، نه لزوماً نکول.
    """
    contracts = pd.read_sql(
        """
        SELECT loanfile_id, grant_date, duration_days
        FROM dbo.vw_Loan_Contract_Dedup
        WHERE duration_days IS NOT NULL AND duration_days > 0 AND LEN(LTRIM(RTRIM(grant_date))) = 10
        """,
        engine,
    )
    balances = pd.read_sql(
        f"""
        SELECT loanfile_id, MAX(Total_Remain) AS balance
        FROM dbo.Loan_Remain
        WHERE Transaction_Date = {LATEST_LOAN_TD}
        GROUP BY loanfile_id
        HAVING MAX(Total_Remain) > 0
        """,
        engine,
    )
    df = contracts.merge(balances, on="loanfile_id", how="inner")
    df["grant_ordinal"] = df["grant_date"].map(jalali_str_to_ordinal)
    df = df.dropna(subset=["grant_ordinal"])
    df["maturity_ordinal"] = df["grant_ordinal"] + df["duration_days"]
    latest_ordinal = jdatetime.date(1404, 12, 29).togregorian().toordinal()
    df["remaining_days"] = df["maturity_ordinal"] - latest_ordinal

    bins = [-10_000_000, 0, 90, 365, 3 * 365, 5 * 365, 10 * 365, 10_000_000]
    labels = ["سررسیدگذشته", "۰-۹۰ روز", "۹۱-۳۶۵ روز (زیر ۱ سال)", "۱-۳ سال", "۳-۵ سال", "۵-۱۰ سال", "بالای ۱۰ سال"]
    df["maturity_bucket"] = pd.cut(df["remaining_days"], bins=bins, labels=labels)

    summary = df.groupby("maturity_bucket", observed=True).agg(
        loan_count=("loanfile_id", "size"), total_balance=("balance", "sum")
    ).reindex(labels).reset_index()
    summary["balance_share_pct"] = (summary["total_balance"] / summary["total_balance"].sum() * 100).round(2)
    print(f"\n=== ۹. پروفایل سررسید تسهیلات (بر مبنای {len(df):,} قرارداد شناخته‌شده، آخرین ماه) ===")
    print(summary.to_string(index=False))
    overdue_pct = summary.loc[summary["maturity_bucket"] == "سررسیدگذشته", "balance_share_pct"].iloc[0]
    print(f"→ {overdue_pct:.1f}٪ مانده‌ی این زیرمجموعه مربوط به قراردادهایی است که از تاریخ سررسید "
          f"برنامه‌ریزی‌شده گذشته‌اند ولی هنوز مانده دارند (تمدید/استمهال یا نکول — قابل‌تفکیک نیست).")

    if not summary.empty:
        save_barh_dual = summary.iloc[::-1]
        fig, ax = plt.subplots(figsize=(10, 6))
        y_pos = range(len(save_barh_dual))
        ax.barh(y_pos, save_barh_dual["balance_share_pct"])
        ax.set_yticks(list(y_pos))
        ax.set_yticklabels([fa(t) for t in save_barh_dual["maturity_bucket"]], fontsize=10)
        ax.set_xlabel(fa("سهم از مانده‌ی شناخته‌شده (درصد)"))
        ax.set_title(fa("پروفایل سررسید تسهیلات — مانده به تفکیک عمر باقی‌مانده‌ی قرارداد"))
        ax.xaxis.set_major_formatter(lambda v, pos: to_persian_digits(f"{v:,.0f}") + "%")
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / "loan_maturity_profile.png", dpi=150)
        plt.close(fig)
    summary.to_csv(PROCESSED_DIR / "loan_maturity_profile.csv", index=False)


def section_10_npl_by_size(engine) -> None:
    """۱۰. NPL به تفکیک اندازه‌ی وام (مبلغ اعطایی) و اندازه‌ی شعبه (چارک مانده‌ی تسهیلات)."""
    # ۱۰.الف — به تفکیک اندازه‌ی وام
    by_loan_size = pd.read_sql(
        f"""
        WITH LatestBalance AS (
            SELECT loanfile_id, MAX(Total_Remain) AS balance, MAX(MANDE_JARI) AS mande_jari
            FROM dbo.Loan_Remain
            WHERE Transaction_Date = {LATEST_LOAN_TD}
            GROUP BY loanfile_id
            HAVING MAX(Total_Remain) > 0
        )
        SELECT
            CASE
                WHEN c.grant_amount < 500000000    THEN N'۱) زیر ۵۰۰ میلیون'
                WHEN c.grant_amount < 2000000000   THEN N'۲) ۵۰۰م تا ۲ میلیارد'
                WHEN c.grant_amount < 10000000000  THEN N'۳) ۲ تا ۱۰ میلیارد'
                WHEN c.grant_amount < 50000000000  THEN N'۴) ۱۰ تا ۵۰ میلیارد'
                ELSE                                     N'۵) بالای ۵۰ میلیارد'
            END AS size_bucket,
            COUNT(*) AS loan_count,
            SUM(lb.balance) AS total_balance,
            SUM(lb.balance - lb.mande_jari) AS npl_balance
        FROM LatestBalance lb
        JOIN dbo.vw_Loan_Contract_Dedup c ON c.loanfile_id = lb.loanfile_id
        WHERE c.grant_amount IS NOT NULL AND c.grant_amount > 0
        GROUP BY
            CASE
                WHEN c.grant_amount < 500000000    THEN N'۱) زیر ۵۰۰ میلیون'
                WHEN c.grant_amount < 2000000000   THEN N'۲) ۵۰۰م تا ۲ میلیارد'
                WHEN c.grant_amount < 10000000000  THEN N'۳) ۲ تا ۱۰ میلیارد'
                WHEN c.grant_amount < 50000000000  THEN N'۴) ۱۰ تا ۵۰ میلیارد'
                ELSE                                     N'۵) بالای ۵۰ میلیارد'
            END
        ORDER BY size_bucket
        """,
        engine,
    )
    by_loan_size["npl_ratio_pct"] = (by_loan_size["npl_balance"] / by_loan_size["total_balance"] * 100).round(1)
    print(f"\n=== ۱۰.الف NPL به تفکیک اندازه‌ی وام (مبلغ اعطایی، بر مبنای {by_loan_size['loan_count'].sum():,} قرارداد شناخته‌شده) ===")
    print(by_loan_size.to_string(index=False))

    fig, ax1 = plt.subplots(figsize=(10, 6))
    x_pos = range(len(by_loan_size))
    ax1.bar(list(x_pos), by_loan_size["total_balance"], color="tab:blue", alpha=0.5, label=fa("مانده‌ی کل"))
    ax1.set_ylabel(fa("مانده‌ی کل (ریال)"), color="tab:blue")
    ax1.yaxis.set_major_formatter(lambda v, pos: to_persian_digits(f"{v:,.0f}"))
    ax2 = ax1.twinx()
    ax2.plot(list(x_pos), by_loan_size["npl_ratio_pct"], color="tab:red", marker="o", linewidth=2, label=fa("نسبت NPL"))
    ax2.set_ylabel(fa("نسبت NPL (درصد)"), color="tab:red")
    ax2.yaxis.set_major_formatter(lambda v, pos: to_persian_digits(f"{v:,.0f}") + "%")
    ax1.set_xticks(list(x_pos))
    ax1.set_xticklabels([fa(t) for t in by_loan_size["size_bucket"]], rotation=20, ha="right", fontsize=8)
    ax1.set_title(fa("نسبت NPL به تفکیک اندازه‌ی وام (مبلغ اعطایی)"))
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "npl_by_loan_size.png", dpi=150)
    plt.close(fig)
    by_loan_size.to_csv(PROCESSED_DIR / "npl_by_loan_size.csv", index=False)

    # ۱۰.ب — به تفکیک اندازه‌ی شعبه (چارک مانده‌ی تسهیلات هر شعبه)
    branch_df = pd.read_sql(
        f"""
        SELECT branch_name, SUM(total_balance) AS loan_balance, SUM(total_npl_balance) AS npl_balance
        FROM dbo.vw_Loan_Remain_By_Branch_Month
        WHERE year_month = {LATEST_MONTH} AND branch_name IS NOT NULL
        GROUP BY branch_name
        HAVING SUM(total_balance) > 0
        """,
        engine,
    )
    branch_df["size_quartile"] = pd.qcut(
        branch_df["loan_balance"], 4,
        labels=["۱) کوچک‌ترین چارک", "۲) چارک متوسط‌رو‌به‌پایین", "۳) چارک متوسط‌رو‌به‌بالا", "۴) بزرگ‌ترین چارک"],
    )
    by_branch_size = branch_df.groupby("size_quartile", observed=True).agg(
        branch_count=("branch_name", "nunique"), total_balance=("loan_balance", "sum"), npl_balance=("npl_balance", "sum")
    ).reset_index()
    by_branch_size["npl_ratio_pct"] = (by_branch_size["npl_balance"] / by_branch_size["total_balance"] * 100).round(1)
    print(f"\n=== ۱۰.ب NPL به تفکیک اندازه‌ی شعبه (چارک بر اساس مانده‌ی تسهیلات هر شعبه، {len(branch_df)} شعبه) ===")
    print(by_branch_size.to_string(index=False))
    biggest_npl = by_branch_size.loc[by_branch_size["npl_ratio_pct"].idxmax(), "size_quartile"]
    print(f"→ بالاترین نسبت NPL در «{biggest_npl}» دیده می‌شود.")

    fig, ax = plt.subplots(figsize=(9, 5))
    x_pos = range(len(by_branch_size))
    ax.bar(list(x_pos), by_branch_size["npl_ratio_pct"], color="tab:orange")
    ax.set_xticks(list(x_pos))
    ax.set_xticklabels([fa(t) for t in by_branch_size["size_quartile"]], rotation=15, ha="right", fontsize=9)
    ax.set_ylabel(fa("نسبت NPL (درصد)"))
    ax.set_title(fa("نسبت NPL به تفکیک اندازه‌ی شعبه (چارک مانده‌ی تسهیلات)"))
    ax.yaxis.set_major_formatter(lambda v, pos: to_persian_digits(f"{v:,.0f}") + "%")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "npl_by_branch_size.png", dpi=150)
    plt.close(fig)
    by_branch_size.to_csv(PROCESSED_DIR / "npl_by_branch_size.csv", index=False)


def section_12_deposit_churn_rate(engine) -> None:
    """۱۲. نرخ ریزش سالانه‌ی سپرده‌گذاران — چند درصد مشتریان فعالِ سال Y، در سال Y+1 دیگر فعال نیستند؟

    ⚠️ تفاوت با کوهورت بخش ب (بند ۵): آنجا ماندگاری *از سال افتتاح حساب تا اسفند ۱۴۰۴* را نشان می‌داد؛
    اینجا گذار *سال‌به‌سال* (Y → Y+1) در کل ۶ سال محاسبه می‌شود — یک مشتری با ۵ سال سابقه هم می‌تواند
    در یک سال میانی «ریزش» کند و دوباره فعال نشود؛ این تحلیل چنین الگویی را نشان می‌دهد.
    «فعال در سال» یعنی حداقل یک ماه از آن سال، مانده‌ی میانگین مثبت داشته است.
    """
    yearly = pd.read_sql(
        """
        SELECT customer_id, CAST(year_mount AS bigint) / 100 AS yr, SUM(avr_total_amount_eq) AS yearly_balance_sum
        FROM dbo.Deposit_Monthly_Activity
        GROUP BY customer_id, CAST(year_mount AS bigint) / 100
        HAVING SUM(avr_total_amount_eq) > 0
        """,
        engine,
    )
    years = sorted(yearly["yr"].unique())
    active_by_year = {yr: set(yearly.loc[yearly["yr"] == yr, "customer_id"]) for yr in years}
    balance_by_year_customer = yearly.set_index(["yr", "customer_id"])["yearly_balance_sum"]

    rows = []
    for y0, y1 in zip(years[:-1], years[1:]):
        active_y0, active_y1 = active_by_year[y0], active_by_year[y1]
        churned = active_y0 - active_y1
        churn_rate_pct = len(churned) / len(active_y0) * 100
        churned_balance = balance_by_year_customer.loc[y0].reindex(list(churned)).sum() if churned else 0
        total_balance_y0 = balance_by_year_customer.loc[y0].sum()
        rows.append({
            "from_year": y0, "to_year": y1,
            "active_customers_start": len(active_y0),
            "churned_customers": len(churned),
            "churn_rate_pct": round(churn_rate_pct, 1),
            "churned_balance_share_pct": round(churned_balance / total_balance_y0 * 100, 2),
        })
    df = pd.DataFrame(rows)
    print("\n=== ۱۲. نرخ ریزش سالانه‌ی سپرده‌گذاران (فعال در سال Y ولی نه در سال Y+1) ===")
    print(df.to_string(index=False))
    print(f"→ میانگین نرخ ریزش سالانه طی ۵ گذار: {df['churn_rate_pct'].mean():.1f}٪")
    print("⚠️ این عدد بسیار پایین‌تر از انتظار به‌نظر می‌رسد چون تعریف «ریزش» اینجا سخت‌گیرانه است: فقط "
          "مشتریانی که مانده‌ی میانگین‌شان در *کل* یک سال دقیقاً صفر شده (حساب کاملاً خالی/بسته) ریزش "
          "محسوب می‌شوند. یک مشتری که فعالیتش کم شده ولی مانده‌ی باقیمانده‌ی کوچکی هنوز دارد، این‌جا "
          "«فعال» طبقه‌بندی می‌شود. برای نرخ ریزشِ رفتاری‌تر (مبتنی بر Recency/آستانه‌ی مانده، مشابه "
          "vw_Active_Depositor_Flags)، باید یک تعریف جداگانه ساخته شود.")

    if not df.empty:
        fig, ax1 = plt.subplots(figsize=(9, 5))
        x_pos = range(len(df))
        # نکته: فونت Vazirmatn گلیف فلش یونیکد را رندر نمی‌کند (باگ تکرارشونده‌ی این پروژه) — «به» جایگزین شد.
        x_labels = [to_persian_digits(f"{int(r.from_year)} به {int(r.to_year)}") for r in df.itertuples()]
        ax1.bar(list(x_pos), df["churn_rate_pct"], color="tab:red", alpha=0.7)
        ax1.set_xticks(list(x_pos))
        ax1.set_xticklabels(x_labels)
        ax1.set_ylabel(fa("نرخ ریزش تعدادی (درصد)"))
        ax1.set_title(fa("نرخ ریزش سالانه‌ی سپرده‌گذاران (سال‌به‌سال)"))
        ax1.yaxis.set_major_formatter(lambda v, pos: to_persian_digits(f"{v:,.1f}") + "%")
        for i, v in enumerate(df["churn_rate_pct"]):
            ax1.annotate(to_persian_digits(f"{v:.1f}") + "%", (i, v), ha="center", va="bottom", fontsize=9)
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / "deposit_annual_churn_rate.png", dpi=150)
        plt.close(fig)
    df.to_csv(PROCESSED_DIR / "deposit_annual_churn_rate.csv", index=False)


def main() -> None:
    engine = get_engine()
    section_8_deposit_balance_ladder(engine)
    section_9_loan_maturity_profile(engine)
    section_10_npl_by_size(engine)
    section_12_deposit_churn_rate(engine)
    print(f"\nخروجی‌ها در {PROCESSED_DIR} و {FIGURES_DIR} ذخیره شدند.")


if __name__ == "__main__":
    main()
