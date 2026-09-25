"""
فاز ۱ — بخش «پ: تحلیلی/پیشرفته» از فهرست پیشنهادی تحلیل‌ها (طرح‌شده و تأییدشده در چت، ۲۰۲۶-۰۹-۰۴):

۱. تحلیل پیچیدگی قرارداد چندضامنی — NPL به تفکیک تعداد ضامن
۲. نوسان مانده‌ی سپرده (Volatility) به‌عنوان شاخص ریسک نقدینگی
۳. ماتریس انتقال ریسک (Transition Matrix) توصیفی — دو مقطع (اسفند ۱۴۰۳ در برابر اسفند ۱۴۰۴)
۴. توزیع DPD (روزهای دیرکرد اقساط)
۵. تحلیل تمرکز/پارتو مشتریان (سپرده و تسهیلات)
۶. کارنامه‌ی ترکیبی عملکرد شعب
۷. نسبت کارمزد به گردش حساب (سودآوری مشتری)

⚠️ نکات کارایی حیاتی (کشف‌شده در نشست‌های ۲۰۲۶-۰۹-۰۴):
- برای dedup چندضامنی روی Loan_Remain، هرگز از ROW_NUMBER() OVER(...) استفاده نکنید — امروز این الگو
  حتی با ایندکس پوششی و MAXDOP 1 در CXSYNC_PORT (قفل هماهنگی Threadهای موازی) گیر کرد و ۶۲+ دقیقه
  بدون نتیجه ماند. به‌جایش از GROUP BY loanfile_id, Transaction_Date + MAX(col) استفاده کنید — چون
  مقادیر مانده در تمام ردیف‌های ضامن‌ها عیناً یکسان‌اند، MAX نتیجه‌ی درست و پلن اجرای پایدار می‌دهد
  (تست شد: کل ۶۰ ماه بدون فیلتر با این روش در ۱۶۱ ثانیه تمام شد، بدون هیچ گیرکردگی).
- هر کوئری‌ای که Transaction_Date/year_month را بدون CAST(...AS bigint) تقسیم می‌کند، نتیجه‌ی اعشاری
  می‌دهد و شرط‌های تساوی را همیشه False می‌کند (باگ تکرارشونده‌ی این پروژه) — این‌بار در WHERE ماتریس
  انتقال هم رخ داد و رفع شد؛ همیشه صریحاً CAST کنید.
- برای DPD (LOAN_MONTHLY_ACTIVITY.payed_date/delivery_date)، تاریخ‌ها شمسی متنی‌اند و باید با jdatetime
  به میلادی تبدیل شوند (طبق docs/03_data_dictionary.md). چون ۱۷ میلیون ردیف خام تبدیل مستقیم را کند
  می‌کند، ابتدا به ۱.۴ میلیون جفت‌تاریخ یکتا GROUP BY می‌شود (~۱۴۴ ثانیه، فقط یک‌بار) و تبدیل روی همان
  جفت‌های یکتا انجام می‌شود؛ برای تفکیک به نوع تسهیلات از TABLESAMPLE (نمونه‌ی آماری ~۱ میلیون ردیفی،
  عملاً آنی) استفاده شده — این بخش صریحاً «برآورد نمونه‌ای» است، نه شمارش دقیق کل جمعیت.
- کوئری‌های فیلترشده به یک ماه از طریق vw_Loan_Remain_By_Branch_Month (نه بدون فیلتر) قابل‌تحمل‌اند
  (~۵۵ ثانیه، تست شد) — فقط نسخه‌ی کاملاً بدون فیلتر (۶۰ ماه هم‌زمان از طریق خودِ View) خطرناک است.

خروجی: نمودار PNG برای هر تحلیل در reports/figures/phase1_market_overview/ و جدول CSV در
data/processed/phase1_market_overview/
"""

from pathlib import Path

import jdatetime
import matplotlib.pyplot as plt
import numpy as np
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
LAST_12M_START = 140401     # فروردین ۱۴۰۴ — شروع ۱۲ ماه اخیرِ کامل

STATUS_LABELS = {
    "jari": "جاری",
    "sarresid": "سررسیدگذشته",
    "moaavagh": "معوق",
    "mashkook": "مشکوک",
    "X": "بدون‌مانده (بسته)",
}
STATUS_ORDER = ["jari", "sarresid", "moaavagh", "mashkook", "X"]


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


def jalali_str_to_ordinal(s: str) -> int | None:
    """رشته‌ی 'YYYY/MM/DD' شمسی را به عدد ترتیبی میلادی (ordinal) تبدیل می‌کند؛ نامعتبر -> None."""
    try:
        y, m, d = (int(p) for p in s.split("/"))
        return jdatetime.date(y, m, d).togregorian().toordinal()
    except (ValueError, TypeError):
        return None


def section_1_guarantor_complexity(engine) -> None:
    """۱. تحلیل پیچیدگی قرارداد چندضامنی — تعداد ضامن هر loanfile_id (آخرین ماه) در برابر نسبت NPL."""
    query = f"""
        WITH OnePerLoan AS (
            SELECT loanfile_id, COUNT(DISTINCT customer_id) AS guarantor_count,
                   MAX(Total_Remain) AS total_remain, MAX(MANDE_JARI) AS mande_jari
            FROM dbo.Loan_Remain
            WHERE Transaction_Date = {LATEST_LOAN_TD}
            GROUP BY loanfile_id
        )
        SELECT
            CASE WHEN guarantor_count = 1 THEN N'۱ (تک‌ضامنی)'
                 WHEN guarantor_count BETWEEN 2 AND 3 THEN N'۲-۳'
                 WHEN guarantor_count BETWEEN 4 AND 6 THEN N'۴-۶'
                 WHEN guarantor_count BETWEEN 7 AND 10 THEN N'۷-۱۰'
                 ELSE N'۱۱+' END AS guarantor_bucket,
            COUNT(*) AS loan_count,
            SUM(total_remain) AS total_balance,
            SUM(total_remain - mande_jari) AS npl_balance,
            SUM(total_remain - mande_jari) * 100.0 / NULLIF(SUM(total_remain), 0) AS npl_ratio_pct
        FROM OnePerLoan
        GROUP BY
            CASE WHEN guarantor_count = 1 THEN N'۱ (تک‌ضامنی)'
                 WHEN guarantor_count BETWEEN 2 AND 3 THEN N'۲-۳'
                 WHEN guarantor_count BETWEEN 4 AND 6 THEN N'۴-۶'
                 WHEN guarantor_count BETWEEN 7 AND 10 THEN N'۷-۱۰'
                 ELSE N'۱۱+' END
    """
    df = pd.read_sql(query, engine)
    order = ["۱ (تک‌ضامنی)", "۲-۳", "۴-۶", "۷-۱۰", "۱۱+"]
    df["guarantor_bucket"] = pd.Categorical(df["guarantor_bucket"], categories=order, ordered=True)
    df = df.sort_values("guarantor_bucket").reset_index(drop=True)
    print("\n=== ۱. پیچیدگی قرارداد چندضامنی — NPL به تفکیک تعداد ضامن (آخرین ماه) ===")
    print(df.to_string(index=False))

    if not df.empty:
        fig, ax1 = plt.subplots(figsize=(9, 5))
        x_pos = range(len(df))
        ax1.bar(list(x_pos), df["loan_count"], color="tab:blue", alpha=0.6, label=fa("تعداد قرارداد"))
        ax1.set_xticks(list(x_pos))
        ax1.set_xticklabels([fa(t) for t in df["guarantor_bucket"]])
        ax1.set_ylabel(fa("تعداد قرارداد"))
        ax1.yaxis.set_major_formatter(lambda v, pos: to_persian_digits(f"{v:,.0f}"))
        ax2 = ax1.twinx()
        ax2.plot(list(x_pos), df["npl_ratio_pct"], color="tab:red", marker="o", linewidth=2, label=fa("نسبت NPL"))
        ax2.set_ylabel(fa("نسبت NPL (درصد)"))
        ax2.yaxis.set_major_formatter(lambda v, pos: to_persian_digits(f"{v:,.0f}") + "%")
        ax1.set_title(fa("پیچیدگی قرارداد چندضامنی: تعداد قرارداد و نسبت NPL به تفکیک تعداد ضامن"))
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / "guarantor_complexity_npl.png", dpi=150)
        plt.close(fig)
    df.to_csv(PROCESSED_DIR / "guarantor_complexity_npl.csv", index=False)


def section_2_deposit_volatility(engine) -> None:
    """۲. نوسان مانده‌ی سپرده (ضریب تغییرات CV = انحراف‌معیار/میانگین) طی ۷۲ ماه، به‌عنوان شاخص ریسک نقدینگی.

    ⚠️ رفع (بازبینی مستقل Claude Opus، ۲۰۲۶-۰۹-۱۱، بند ۲.۱۱): نسخه‌ی اول فقط مانده‌ی میانگین دقیقاً صفر
    را حذف می‌کرد؛ حساب‌های نزدیک‌به‌صفر (مثلاً میانگین ۱۰۰,۰۰۰ ریال) با کوچک‌ترین نوسان مطلق هم CV
    بسیار بزرگی می‌گیرند و سطل «بحرانی» را مصنوعاً پر می‌کردند (نه رفتار واقعی ریسک). حداقل مانده‌ی
    ۵ میلیون ریال اضافه شد — همان آستانه‌ی «مشتری فعال» در docs/07_sampling_methodology.md.
    """
    query = """
        SELECT customer_id, AVG(avr_total_amount_eq) AS mean_balance, STDEV(avr_total_amount_eq) AS sd_balance
        FROM dbo.Deposit_Monthly_Activity
        GROUP BY customer_id
        HAVING AVG(avr_total_amount_eq) >= 5000000 AND COUNT(*) >= 6
    """
    raw = pd.read_sql(query, engine)
    raw["cv"] = raw["sd_balance"] / raw["mean_balance"]

    bins = [-0.001, 0.25, 0.5, 1.0, 2.0, float("inf")]
    labels = ["کم‌نوسان (<۰.۲۵)", "متوسط (۰.۲۵-۰.۵)", "بالا (۰.۵-۱)", "خیلی‌بالا (۱-۲)", "بحرانی (>۲)"]
    raw["volatility_bucket"] = pd.cut(raw["cv"], bins=bins, labels=labels)

    df = (
        raw.groupby("volatility_bucket", observed=True)
        .agg(customer_count=("customer_id", "size"), total_balance=("mean_balance", "sum"))
        .reset_index()
    )
    df["customer_share_pct"] = (df["customer_count"] / df["customer_count"].sum() * 100).round(2)
    df["balance_share_pct"] = (df["total_balance"] / df["total_balance"].sum() * 100).round(2)
    print("\n=== ۲. توزیع نوسان مانده‌ی سپرده (ضریب تغییرات CV، ۷۲ ماه) ===")
    print(df.to_string(index=False))
    high_vol_balance_share = df.loc[df["volatility_bucket"].isin(["خیلی‌بالا (۱-۲)", "بحرانی (>۲)"]), "balance_share_pct"].sum()
    print(f"→ {high_vol_balance_share:.1f}٪ از کل مانده‌ی میانگین متعلق به مشتریان با نوسان خیلی‌بالا/بحرانی است.")

    if not df.empty:
        save_barh(df.iloc[::-1], "volatility_bucket", "customer_share_pct",
                   "توزیع مشتریان سپرده‌گذار بر اساس نوسان مانده (ضریب تغییرات، ۷۲ ماه)",
                   "سهم مشتریان (درصد)", "deposit_volatility_distribution.png")
    df.to_csv(PROCESSED_DIR / "deposit_volatility_distribution.csv", index=False)


def section_3_transition_matrix(engine) -> None:
    """۳. ماتریس انتقال ریسک توصیفی — دو مقطع: بهمن→اسفند ۱۴۰۳ و بهمن→اسفند ۱۴۰۴ (برای مقایسه‌ی روند)."""
    query = """
        WITH Base AS (
            SELECT loanfile_id, Transaction_Date,
                MAX(MANDE_JARI) AS mande_jari, MAX(Overusance_Remain) AS overusance,
                MAX(Postponed_Remain) AS postponed, MAX(Doubtful_Remain) AS doubtful,
                MAX(Total_Remain) AS total_remain
            FROM dbo.Loan_Remain
            WHERE CAST(Transaction_Date AS bigint) / 100 IN (140311, 140312, 140411, 140412)
            GROUP BY loanfile_id, Transaction_Date
        ),
        Classified AS (
            SELECT loanfile_id, Transaction_Date,
                CASE WHEN total_remain <= 0 THEN N'X'
                     WHEN doubtful > 0 THEN N'mashkook'
                     WHEN postponed > 0 THEN N'moaavagh'
                     WHEN overusance > 0 THEN N'sarresid'
                     ELSE N'jari' END AS status
            FROM Base
        )
        SELECT
            CAST(c1.Transaction_Date AS bigint) / 100 AS from_year_month,
            c1.status AS from_status, c2.status AS to_status, COUNT(*) AS cnt
        FROM Classified c1
        JOIN Classified c2 ON c2.loanfile_id = c1.loanfile_id
        WHERE (CAST(c1.Transaction_Date AS bigint) / 100 = 140311 AND CAST(c2.Transaction_Date AS bigint) / 100 = 140312)
           OR (CAST(c1.Transaction_Date AS bigint) / 100 = 140411 AND CAST(c2.Transaction_Date AS bigint) / 100 = 140412)
        GROUP BY CAST(c1.Transaction_Date AS bigint) / 100, c1.status, c2.status
    """
    df = pd.read_sql(query, engine)
    print("\n=== ۳. ماتریس انتقال ریسک — تعداد قرارداد بر اساس طبقه‌ی ماه قبل در برابر ماه بعد ===")
    print(df.to_string(index=False))
    df.to_csv(PROCESSED_DIR / "transition_matrix_raw.csv", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    # نکته: فونت Vazirmatn گلیف فلش یونیکد (→) را ندارد؛ از «تا» به‌جای فلش استفاده شد.
    for ax, from_ym, title in zip(axes, [140311, 140411], ["بهمن تا اسفند ۱۴۰۳", "بهمن تا اسفند ۱۴۰۴"]):
        sub = df[df["from_year_month"] == from_ym]
        pivot = sub.pivot_table(index="from_status", columns="to_status", values="cnt", fill_value=0)
        pivot = pivot.reindex(index=STATUS_ORDER, columns=STATUS_ORDER, fill_value=0)
        row_pct = pivot.div(pivot.sum(axis=1).replace(0, np.nan), axis=0) * 100
        im = ax.imshow(row_pct.values, cmap="YlOrRd", vmin=0, vmax=100)
        ax.set_xticks(range(len(STATUS_ORDER)))
        ax.set_yticks(range(len(STATUS_ORDER)))
        ax.set_xticklabels([fa(STATUS_LABELS[s]) for s in STATUS_ORDER], rotation=45, ha="right", fontsize=8)
        ax.set_yticklabels([fa(STATUS_LABELS[s]) for s in STATUS_ORDER], fontsize=8)
        ax.set_title(fa(title), fontsize=10)
        for i in range(len(STATUS_ORDER)):
            for j in range(len(STATUS_ORDER)):
                val = row_pct.values[i, j]
                if not np.isnan(val):
                    ax.text(j, i, to_persian_digits(f"{val:.0f}"), ha="center", va="center", fontsize=7,
                            color="white" if val > 50 else "black")
    fig.suptitle(fa("ماتریس انتقال ریسک (درصد ردیفی) — مقایسه‌ی همان بازه در دو سال متوالی"))
    fig.colorbar(im, ax=axes, shrink=0.7, label=fa("درصد انتقال"))
    fig.savefig(FIGURES_DIR / "risk_transition_matrix.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def classify_dpd(dpd: pd.Series) -> pd.Series:
    """طبقه‌بندی DPD با در نظر گرفتن ردیف‌های «قسط آتی» (شرح کامل زیر).

    ⚠️ یافته‌ی کیفیت داده (نشست ۲۰۲۶-۰۹-۰۴، حین ساخت این بخش کشف شد): delivery_date در
    Loan_Monthly_Activity برای بخش بزرگی از ردیف‌ها (تأیید شد با Status='Jari') تا ۱۰+ سال در
    آینده است — یعنی این جدول شامل اقساط برنامه‌ریزی‌شده‌ی آتی هم هست، نه فقط اقساط سررسیدشده/
    پرداخت‌شده. برای این ردیف‌ها payed_date−delivery_date یک عدد منفی بسیار بزرگ و بی‌معنا می‌دهد
    (نمونه‌ی تأییدی: قسط جعاله با delivery_date سال ۱۴۱۶، payed_date سال ۱۴۰۵). این ردیف‌ها را
    باید صریحاً به‌عنوان «قسط آتی/سررسیدنشده» طبقه‌بندی کرد، نه در میانگین DPD لحاظ کرد.
    """
    bins = [-10_000_000, -30, 0, 7, 30, 90, 10_000_000]
    labels = [
        "قسط آتی (سررسید نشده)", "پرداخت زودتر (تا ۳۰ روز)", "۱-۷ روز دیرکرد",
        "۸-۳۰ روز دیرکرد", "۳۱-۹۰ روز دیرکرد", "بیش از ۹۰ روز دیرکرد",
    ]
    return pd.cut(dpd, bins=bins, labels=labels)


def section_4_dpd_distribution(engine) -> None:
    """۴. توزیع DPD (روزهای دیرکرد پرداخت قسط نسبت به سررسید) — کل جمعیت (دقیق) + به تفکیک نوع (نمونه‌ای)."""
    pair_query = """
        SELECT
            LTRIM(RTRIM(REPLACE(payed_date, CHAR(34), ''))) AS pd,
            LTRIM(RTRIM(REPLACE(delivery_date, CHAR(34), ''))) AS dd,
            COUNT(*) AS cnt
        FROM dbo.Loan_Monthly_Activity
        GROUP BY LTRIM(RTRIM(REPLACE(payed_date, CHAR(34), ''))), LTRIM(RTRIM(REPLACE(delivery_date, CHAR(34), '')))
    """
    pairs = pd.read_sql(pair_query, engine)
    pairs["pd_ord"] = pairs["pd"].map(jalali_str_to_ordinal)
    pairs["dd_ord"] = pairs["dd"].map(jalali_str_to_ordinal)
    pairs = pairs.dropna(subset=["pd_ord", "dd_ord"])
    pairs["dpd"] = pairs["pd_ord"] - pairs["dd_ord"]
    pairs["dpd_bucket"] = classify_dpd(pairs["dpd"])

    dist = pairs.groupby("dpd_bucket", observed=True)["cnt"].sum().reset_index()
    dist["share_pct"] = (dist["cnt"] / dist["cnt"].sum() * 100).round(2)
    print("\n=== ۴.الف توزیع DPD (روزهای دیرکرد) — کل جمعیت اقساط، محاسبه‌ی دقیق ===")
    print(dist.to_string(index=False))
    future_share = dist.loc[dist["dpd_bucket"] == "قسط آتی (سررسید نشده)", "share_pct"].sum()
    print(f"→ {future_share:.1f}٪ از کل ردیف‌های این جدول در واقع اقساط آتی/سررسیدنشده‌اند (نه رویداد پرداخت واقعی).")
    due_dist = dist[dist["dpd_bucket"] != "قسط آتی (سررسید نشده)"].copy()
    due_dist["share_of_due_pct"] = (due_dist["cnt"] / due_dist["cnt"].sum() * 100).round(2)
    print("\nتوزیع فقط در میان اقساط واقعاً سررسیدشده (بدون اقساط آتی):")
    print(due_dist.to_string(index=False))

    if not dist.empty:
        save_barh(dist.iloc[::-1], "dpd_bucket", "share_pct",
                   "توزیع روزهای دیرکرد پرداخت قسط (DPD) — کل جمعیت اقساط (شامل اقساط آتی)",
                   "سهم از کل ردیف‌ها (درصد)", "dpd_distribution_overall.png")
    dist.to_csv(PROCESSED_DIR / "dpd_distribution_overall.csv", index=False)
    due_dist.to_csv(PROCESSED_DIR / "dpd_distribution_due_only.csv", index=False)

    # ⚠️ به تفکیک نوع تسهیلات: بر مبنای نمونه‌ی آماری (TABLESAMPLE ~۱ میلیون ردیف)، نه کل جمعیت —
    # تبدیل جالی-به-میلادی برای کل ۱۷ میلیون ردیف خام مقرون‌به‌صرفه نبود.
    sample_query = """
        SELECT
            LTRIM(RTRIM(REPLACE(m.payed_date, CHAR(34), ''))) AS pd,
            LTRIM(RTRIM(REPLACE(m.delivery_date, CHAR(34), ''))) AS dd,
            c.loan_type_description
        FROM dbo.Loan_Monthly_Activity m TABLESAMPLE (1000000 ROWS)
        JOIN dbo.vw_Loan_Contract_Dedup c ON c.loanfile_id = m.loanfile_id
    """
    sample = pd.read_sql(sample_query, engine)
    sample["pd_ord"] = sample["pd"].map(jalali_str_to_ordinal)
    sample["dd_ord"] = sample["dd"].map(jalali_str_to_ordinal)
    sample = sample.dropna(subset=["pd_ord", "dd_ord"])
    sample["dpd"] = sample["pd_ord"] - sample["dd_ord"]

    conditions = [
        sample["loan_type_description"].str.contains("قرض الحسنه", na=False),
        sample["loan_type_description"].str.contains("مرابحه", na=False),
        sample["loan_type_description"].str.contains("مشارکت مدني", na=False),
        sample["loan_type_description"].str.contains("فروش اقساطي", na=False),
        sample["loan_type_description"].str.contains("جعاله", na=False),
        sample["loan_type_description"].str.contains("مضاربه", na=False),
        sample["loan_type_description"].str.contains("استصناع", na=False),
    ]
    choices = ["قرض‌الحسنه", "مرابحه", "مشارکت مدنی", "فروش اقساطی", "جعاله", "مضاربه", "استصناع"]
    sample["loan_type_group"] = np.select(conditions, choices, default="سایر")

    # فقط اقساط واقعاً سررسیدشده (dpd >= -30) در میانگین لحاظ می‌شوند؛ سهم اقساط آتی هر نوع جداگانه گزارش می‌شود.
    sample["is_future"] = sample["dpd"] < -30
    future_by_type = sample.groupby("loan_type_group")["is_future"].mean().mul(100).round(1).rename("future_share_pct")
    due_sample = sample[~sample["is_future"]]
    by_type = due_sample.groupby("loan_type_group").agg(
        due_sample_size=("dpd", "size"), avg_dpd_days=("dpd", "mean")
    ).reset_index()
    by_type = by_type.merge(future_by_type, on="loan_type_group", how="left").sort_values("avg_dpd_days", ascending=False)
    print("\n=== ۴.ب میانگین DPD (فقط اقساط سررسیدشده) و سهم اقساط آتی، به تفکیک نوع (برآورد نمونه‌ای) ===")
    print(by_type.to_string(index=False))
    if not by_type.empty:
        save_barh(by_type.sort_values("avg_dpd_days"), "loan_type_group", "avg_dpd_days",
                   "میانگین DPD اقساط سررسیدشده به تفکیک نوع تسهیلات — برآورد نمونه‌ای",
                   "میانگین DPD (روز)", "dpd_by_loan_type.png")
    by_type.to_csv(PROCESSED_DIR / "dpd_by_loan_type.csv", index=False)


def section_5_concentration_pareto(engine) -> None:
    """۵. تحلیل تمرکز/پارتو مشتریان — چه سهمی از مانده‌ی کل در دست چه سهمی از مشتریان است (سپرده و تسهیلات)."""
    deposit_df = pd.read_sql(
        f"""
        SELECT customer_id, SUM(avr_total_amount_eq) AS balance
        FROM dbo.Deposit_Monthly_Activity
        WHERE year_mount = {LATEST_MONTH}
        GROUP BY customer_id
        HAVING SUM(avr_total_amount_eq) > 0
        """,
        engine,
    )
    loan_df = pd.read_sql(
        f"""
        SELECT customer_id, SUM(Total_Remain) AS balance
        FROM dbo.Loan_Remain
        WHERE Transaction_Date = {LATEST_LOAN_TD}
        GROUP BY customer_id
        HAVING SUM(Total_Remain) > 0
        """,
        engine,
    )

    def lorenz_curve(df: pd.DataFrame) -> pd.DataFrame:
        sorted_balance = df["balance"].sort_values(ascending=False).reset_index(drop=True)
        cum_customers_pct = (np.arange(1, len(sorted_balance) + 1) / len(sorted_balance)) * 100
        cum_balance_pct = (sorted_balance.cumsum() / sorted_balance.sum()) * 100
        return pd.DataFrame({"cum_customers_pct": cum_customers_pct, "cum_balance_pct": cum_balance_pct})

    deposit_lorenz = lorenz_curve(deposit_df)
    loan_lorenz = lorenz_curve(loan_df)

    summary_rows = []
    for name, lorenz in [("سپرده", deposit_lorenz), ("تسهیلات", loan_lorenz)]:
        for top_pct in [1, 5, 10, 20]:
            idx = (lorenz["cum_customers_pct"] <= top_pct).sum()
            idx = max(idx, 1)
            summary_rows.append({
                "type": name, "top_customers_pct": top_pct,
                "balance_share_pct": round(lorenz["cum_balance_pct"].iloc[idx - 1], 1),
            })
    summary = pd.DataFrame(summary_rows)
    print("\n=== ۵. تحلیل تمرکز/پارتو — سهم مانده‌ی کل در دست بالاترین درصدهای مشتریان (آخرین ماه) ===")
    print(summary.to_string(index=False))
    summary.to_csv(PROCESSED_DIR / "concentration_pareto_summary.csv", index=False)

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.plot(deposit_lorenz["cum_customers_pct"], deposit_lorenz["cum_balance_pct"], label=fa("سپرده"), linewidth=2)
    ax.plot(loan_lorenz["cum_customers_pct"], loan_lorenz["cum_balance_pct"], label=fa("تسهیلات"), linewidth=2)
    ax.plot([0, 100], [0, 100], linestyle="--", color="gray", label=fa("توزیع کاملاً برابر (خط مرجع)"))
    ax.set_xlabel(fa("سهم تجمعی مشتریان (درصد، مرتب‌شده نزولی بر اساس مانده)"))
    ax.set_ylabel(fa("سهم تجمعی مانده (درصد)"))
    ax.set_title(fa("منحنی تمرکز (Lorenz) مانده‌ی سپرده و تسهیلات — آخرین ماه"))
    ax.xaxis.set_major_formatter(lambda v, pos: to_persian_digits(f"{v:,.0f}") + "%")
    ax.yaxis.set_major_formatter(lambda v, pos: to_persian_digits(f"{v:,.0f}") + "%")
    ax.legend(prop={"family": "Vazirmatn"})
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "concentration_lorenz_curve.png", dpi=150)
    plt.close(fig)


def section_6_branch_scorecard(engine) -> None:
    """۶. کارنامه‌ی ترکیبی عملکرد شعب — حجم تسهیلات (اندازه) در برابر نسبت NPL (کیفیت)، با سود سپرده به‌عنوان اندازه‌ی حباب.

    ⚠️ یافته‌ی کیفیت داده‌ی تازه (نشست ۲۰۲۶-۰۹-۰۴): چند واحد اداری/ستادی (مثل «امور حقوقی»،
    «بین‌الملل»، «کارت»، «مدیریت مالی و خزانه»، «مستقل مرکزی») در Base_Branch با
    branch_org_level='شعبه' ثبت شده‌اند (نه 'ستاد'/'سرپرستی')، یعنی فیلتر ساده روی این ستون کافی
    نیست تا شعب واقعی از واحدهای اداری تفکیک شوند. یکی از این واحدها («مستقل مرکزی») حجم بسیار
    بزرگ‌تری از هر شعبه‌ی واقعی دارد و محور را با مقیاس خطی بی‌فایده می‌کرد — به همین دلیل محور x
    (حجم تسهیلات) لگاریتمی شد، نه حذف رکورد (چون نمی‌توان با قطعیت لیست کامل واحدهای اداری را
    بدون تأیید بانک تعیین کرد). برای فاز بعد: از بانک لیست دقیق واحدهای غیرشعبه‌ای درخواست شود.
    """
    loan_by_branch = pd.read_sql(
        f"""
        SELECT branch_name, SUM(total_balance) AS loan_balance, SUM(total_npl_balance) AS npl_balance,
               SUM(loan_count) AS loan_count
        FROM dbo.vw_Loan_Remain_By_Branch_Month
        WHERE year_month = {LATEST_MONTH} AND branch_name IS NOT NULL
        GROUP BY branch_name
        """,
        engine,
    )
    loan_by_branch["npl_ratio_pct"] = (loan_by_branch["npl_balance"] / loan_by_branch["loan_balance"] * 100).round(1)

    deposit_interest = pd.read_sql(
        """
        SELECT b.branch_name, SUM(ibs.Amount) AS deposit_interest_paid
        FROM dbo.Interset_branch_sum ibs
        JOIN dbo.vw_Branch_Dim b
            ON b.branch_code = LTRIM(RTRIM(REPLACE(REPLACE(ibs.BranchCode, CHAR(13), ''), CHAR(10), '')))
        WHERE REPLACE(REPLACE(ibs.Year_Mounth, CHAR(13), ''), CHAR(10), '') = '1404/12'
        GROUP BY b.branch_name
        """,
        engine,
    )

    scorecard = loan_by_branch.merge(deposit_interest, on="branch_name", how="left")
    scorecard["deposit_interest_paid"] = scorecard["deposit_interest_paid"].fillna(0)
    top30 = scorecard.sort_values("loan_balance", ascending=False).head(30).reset_index(drop=True)
    print("\n=== ۶. کارنامه‌ی ترکیبی عملکرد شعب — Top ۳۰ بر اساس حجم تسهیلات (آخرین ماه) ===")
    print(top30[["branch_name", "loan_balance", "npl_ratio_pct", "deposit_interest_paid"]].to_string(index=False))
    scorecard.to_csv(PROCESSED_DIR / "branch_scorecard.csv", index=False)

    fig, ax = plt.subplots(figsize=(11, 8))
    sizes = (top30["deposit_interest_paid"] / top30["deposit_interest_paid"].max() * 800).clip(lower=20)
    scatter = ax.scatter(top30["loan_balance"], top30["npl_ratio_pct"], s=sizes, alpha=0.6, c=top30["npl_ratio_pct"],
                          cmap="YlOrRd", edgecolors="black", linewidths=0.5)
    # برچسب‌گذاری هم Top-10 بر اساس حجم و هم Top-5 بر اساس NPL (شعب کوچک ولی پرریسک هم دیده شوند)
    labeled = pd.concat([top30.head(10), top30.nlargest(5, "npl_ratio_pct")]).drop_duplicates("branch_name")
    for _, row in labeled.iterrows():
        ax.annotate(fa(row["branch_name"]), (row["loan_balance"], row["npl_ratio_pct"]), fontsize=7,
                    xytext=(5, 5), textcoords="offset points")
    ax.set_xscale("log")
    ax.set_xlabel(fa("مانده‌ی تسهیلات (ریال، مقیاس لگاریتمی)"))
    ax.set_ylabel(fa("نسبت NPL (درصد)"))
    ax.set_title(fa("کارنامه‌ی ترکیبی Top-30 شعبه: حجم تسهیلات × کیفیت (NPL) × سود سپرده (اندازه‌ی حباب)"))
    ax.xaxis.set_major_formatter(lambda v, pos: to_persian_digits(f"{v:,.0f}"))
    ax.yaxis.set_major_formatter(lambda v, pos: to_persian_digits(f"{v:,.0f}") + "%")
    fig.colorbar(scatter, ax=ax, label=fa("نسبت NPL (درصد)"))
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "branch_scorecard_bubble.png", dpi=150)
    plt.close(fig)


def section_7_fee_to_turnover(engine) -> None:
    """۷. نسبت کارمزد به گردش کلی حساب (سودآوری کارمزدی مشتری)، ۱۲ ماه اخیر.

    ⚠️ جمعیت این تحلیل محدود به مشتریان دیده‌شده در Customer_Monthly_Activity است (طبق docs/11،
    این جدول فقط زیرمجموعه‌ای از کل مشتریان را پوشش می‌دهد)، نه کل جمعیت سپرده‌گذار/تسهیلات‌گیرنده.
    """
    query = f"""
        WITH FeeByCustomer AS (
            SELECT main_customer_id AS customer_id, SUM(amount_eq) AS total_fee
            FROM dbo.Customer_Monthly_Activity
            WHERE CAST(year_mount AS bigint) BETWEEN {LAST_12M_START} AND {LATEST_MONTH}
            GROUP BY main_customer_id
        ),
        TurnoverByCustomer AS (
            SELECT main_customer_id AS customer_id,
                   SUM(sum_creditor_circul_amount_eq + sum_debtor_circul_amount_eq) AS total_turnover
            FROM (
                SELECT DISTINCT main_customer_id, year_mount, sum_creditor_circul_amount_eq, sum_debtor_circul_amount_eq
                FROM dbo.Customer_Monthly_Activity
                WHERE CAST(year_mount AS bigint) BETWEEN {LAST_12M_START} AND {LATEST_MONTH}
            ) x
            GROUP BY main_customer_id
        )
        SELECT f.customer_id, f.total_fee, t.total_turnover,
               f.total_fee * 100.0 / NULLIF(t.total_turnover, 0) AS fee_ratio_pct
        FROM FeeByCustomer f
        JOIN TurnoverByCustomer t ON t.customer_id = f.customer_id
        WHERE t.total_turnover > 0
    """
    df = pd.read_sql(query, engine)
    print(f"\n=== ۷. نسبت کارمزد به گردش حساب — {len(df):,} مشتری (۱۲ ماه اخیر، جمعیت محدود Customer_Monthly_Activity) ===")
    print(df["fee_ratio_pct"].describe().to_string())

    bins = [-0.001, 0.01, 0.05, 0.1, 0.5, float("inf")]
    labels = ["<۰.۰۱٪", "۰.۰۱-۰.۰۵٪", "۰.۰۵-۰.۱٪", "۰.۱-۰.۵٪", "بالای ۰.۵٪"]
    df["ratio_bucket"] = pd.cut(df["fee_ratio_pct"], bins=bins, labels=labels)
    dist = df.groupby("ratio_bucket", observed=True).size().reset_index(name="customer_count")
    dist["share_pct"] = (dist["customer_count"] / dist["customer_count"].sum() * 100).round(2)
    print(dist.to_string(index=False))

    top10 = df.sort_values("fee_ratio_pct", ascending=False).head(10)
    print("\nTop 10 مشتری با بالاترین نسبت کارمزد به گردش:")
    print(top10.to_string(index=False))

    if not dist.empty:
        save_barh(dist.iloc[::-1], "ratio_bucket", "share_pct",
                   "توزیع مشتریان بر اساس نسبت کارمزد به گردش کلی حساب (۱۲ ماه اخیر)",
                   "سهم مشتریان (درصد)", "fee_to_turnover_distribution.png")
    df.to_csv(PROCESSED_DIR / "fee_to_turnover_ratio.csv", index=False)
    dist.to_csv(PROCESSED_DIR / "fee_to_turnover_distribution.csv", index=False)


def main() -> None:
    engine = get_engine()
    section_1_guarantor_complexity(engine)
    section_2_deposit_volatility(engine)
    section_3_transition_matrix(engine)
    section_4_dpd_distribution(engine)
    section_5_concentration_pareto(engine)
    section_6_branch_scorecard(engine)
    section_7_fee_to_turnover(engine)
    print(f"\nهمه‌ی خروجی‌های بخش پ در {PROCESSED_DIR} و {FIGURES_DIR} ذخیره شدند.")


if __name__ == "__main__":
    main()
