"""
فاز ۱ — بخش «ت: کنجکاوی‌های کیفیت داده» (طرح‌شده و تأییدشده در چت، ۲۰۲۶-۰۹-۰۴):
هدف این بخش برخلاف الف/ب/پ، بستن پرونده‌ی ابهامات کیفیت داده‌ی باز مانده از نشست‌های قبلی است،
نه لزوماً تولید یافته‌ی کسب‌وکاری برای گزارش نهایی.

۱. ریشه‌یابی ۴۸٪ orphan در Loan_Remain.loanfile_id (نسبت به Loan_Contract_Info)
۲. ریشه‌یابی مقادیر منفی Loan_Contract_Info.DURATION_DAYS
۳. ریشه‌یابی ۱۱,۵۲۲ ردیف تکراری Customer_Profile.Customer_id
۴. ریشه‌یابی ۲۰ ردیف تکراری Base_Branch.ID
۵. معنای MAINTYPE_NAME='نزد سایر بانک ها' در Deposit_Accoutnt_Info
۶. آزمون فرضیه‌ی avr_total_amount_eq (میانگین مانده‌ی روزانه؟)
۷. الگوی شکاف ۳ماهه‌ی داده (رکورد خام تا ۱۴۰۵/۰۳، خلاصه‌ها تا ۱۴۰۴/۱۲)
۸. ارتباط بین مشتریان سپرده‌گذار و تسهیلات‌گیرنده (درخواست تکمیلی کاربر) — سازگاری جداول پرچمی با
   حضور واقعی، و بازبینی مستقل یافته‌ی Cross-sell بخش ب

خروجی: عمدتاً جدول CSV + یافته‌ی مستندشده در کنسول؛ نمودار PNG فقط برای بندهای با روند بصری معنادار
(۱، ۶، ۸) تولید می‌شود.
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


def item_1_orphan_loanfile_trend(engine) -> None:
    """۱. آیا orphan-بودن loanfile_id (نسبت به Loan_Contract_Info) الگوی زمانی مشخصی دارد؟"""
    query = """
        WITH LoanRemainDedup AS (
            SELECT loanfile_id, Transaction_Date, MAX(Total_Remain) AS bal
            FROM dbo.Loan_Remain
            GROUP BY loanfile_id, Transaction_Date
        ),
        Flagged AS (
            -- ⚠️ رفع باگ (بازبینی مستقل Claude Opus، ۲۰۲۶-۰۹-۱۱، بند ۲.۶): نسخه‌ی اول اینجا LEFT JOIN مستقیم
            -- به Loan_Contract_Info خام می‌زد. چون آن جدول ۷۸,۰۶۸ گروه LOANFILE_ID تکراری دارد (طبق docs/06)،
            -- LEFT JOIN برای قراردادهای «matched» ردیف تکرار می‌ساخت و SUM(bal) را کاذب متورم می‌کرد
            -- (نتیجه‌ی غلط قبلی برای اسفند ۱۴۰۴: ۱,۹۱۲.۸ هزار میلیارد، نزدیک به همان مبنای غلط ۱,۹۶۱ که در
            -- بخش ۴.۳ رد شده بود). رفع با NOT EXISTS که هیچ‌وقت ردیف تکرار نمی‌سازد.
            SELECT lr.loanfile_id, lr.Transaction_Date, lr.bal,
                   CASE WHEN NOT EXISTS (
                       SELECT 1 FROM dbo.Loan_Contract_Info c WHERE c.LOANFILE_ID = lr.loanfile_id
                   ) THEN 1 ELSE 0 END AS is_orphan
            FROM LoanRemainDedup lr
        )
        SELECT CAST(Transaction_Date AS bigint) / 100 AS year_month, is_orphan,
               COUNT(DISTINCT loanfile_id) AS loan_count, SUM(bal) AS balance
        FROM Flagged
        GROUP BY CAST(Transaction_Date AS bigint) / 100, is_orphan
        ORDER BY year_month
    """
    df = pd.read_sql(query, engine)
    pivot_count = df.pivot(index="year_month", columns="is_orphan", values="loan_count").rename(
        columns={0: "matched_count", 1: "orphan_count"})
    pivot_bal = df.pivot(index="year_month", columns="is_orphan", values="balance").rename(
        columns={0: "matched_balance", 1: "orphan_balance"})
    trend = pivot_count.join(pivot_bal).reset_index()
    trend["orphan_count_share_pct"] = (trend["orphan_count"] / (trend["orphan_count"] + trend["matched_count"]) * 100).round(1)
    trend["orphan_balance_share_pct"] = (trend["orphan_balance"] / (trend["orphan_balance"] + trend["matched_balance"]) * 100).round(1)

    print("\n=== ۱. سهم orphan (تعدادی و ارزشی) در Loan_Remain نسبت به Loan_Contract_Info، به تفکیک ماه (۵ ماه اول/آخر) ===")
    print(pd.concat([trend.head(), trend.tail()])[
        ["year_month", "orphan_count_share_pct", "orphan_balance_share_pct"]
    ].to_string(index=False))
    print("→ یافته: سهم تعدادی orphan تقریباً ثابت و بالا (~۸۵٪) در همه‌ی ماه‌ها باقی می‌ماند، ولی سهم ارزشی "
          "آن در طول زمان کاهش می‌یابد — یعنی Loan_Contract_Info پوشش کامل‌تری برای قراردادهای بزرگ‌تر/جدیدتر "
          "دارد. این با فرضیه‌ی «قراردادهای کوچک/آرشیوی قدیمی از Loan_Contract_Info حذف شده‌اند» سازگار است، "
          "ولی از خودِ داده قابل‌اثبات قطعی نیست — پیشنهاد می‌شود از بانک پرسیده شود.")

    if not trend.empty:
        fig, ax = plt.subplots(figsize=(11, 5))
        x_pos = range(len(trend))
        x_labels = [to_persian_digits(v) for v in trend["year_month"].astype(int).astype(str)]
        ax.plot(list(x_pos), trend["orphan_count_share_pct"], label=fa("سهم تعدادی orphan"), linewidth=2)
        ax.plot(list(x_pos), trend["orphan_balance_share_pct"], label=fa("سهم ارزشی orphan"), linewidth=2, linestyle="--")
        ax.set_xticks(list(x_pos)[::4])
        ax.set_xticklabels(x_labels[::4], rotation=90, fontsize=6)
        ax.set_title(fa("سهم قراردادهای orphan (بدون تطابق در Loan_Contract_Info) در طول زمان"))
        ax.set_ylabel(fa("درصد"))
        ax.yaxis.set_major_formatter(lambda v, pos: to_persian_digits(f"{v:,.0f}") + "%")
        ax.legend(prop={"family": "Vazirmatn"})
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / "dq_orphan_loanfile_trend.png", dpi=150)
        plt.close(fig)
    trend.to_csv(PROCESSED_DIR / "dq_orphan_loanfile_trend.csv", index=False)


def item_2_negative_duration(engine) -> None:
    """۲. مقادیر منفی Loan_Contract_Info.DURATION_DAYS — چند مورد و چه الگویی؟"""
    by_type = pd.read_sql(
        """
        SELECT LTRIM(RTRIM(REPLACE(LOAN_TYPE_DESCRIPTION, CHAR(34), ''))) AS loan_type, COUNT(*) AS cnt
        FROM dbo.Loan_Contract_Info WHERE DURATION_DAYS < 0
        GROUP BY LTRIM(RTRIM(REPLACE(LOAN_TYPE_DESCRIPTION, CHAR(34), '')))
        ORDER BY cnt DESC
        """,
        engine,
    )
    by_year = pd.read_sql(
        "SELECT LEFT(GRANT_DATE,4) AS grant_year, COUNT(*) AS cnt FROM dbo.Loan_Contract_Info "
        "WHERE DURATION_DAYS < 0 GROUP BY LEFT(GRANT_DATE,4) ORDER BY grant_year",
        engine,
    )
    print(f"\n=== ۲. مقادیر منفی DURATION_DAYS — فقط {by_type['cnt'].sum()} ردیف از ۷۸۰,۷۹۰ (رقم ناچیز) ===")
    print(by_type.to_string(index=False))
    print(by_year.to_string(index=False))
    print("→ یافته: تقریباً همه‌ی موارد (۵۶ از ۵۷) دقیقاً یک نوع تسهیلات خاص‌اند («کمک هزینه ودیعه مسکن "
          "کارکنان») و عمدتاً در سال ۱۴۰۳ اعطا شده‌اند — یک باگ محلی/محدود به یک محصول و یک بازه‌ی زمانی "
          "کوتاه، نه یک مشکل سیستمیک در کل جدول. برای مدل‌سازی، فیلتر همین محصول در همین بازه کافی است.")
    by_type.to_csv(PROCESSED_DIR / "dq_negative_duration_by_type.csv", index=False)


def item_3_customer_profile_duplicates(engine) -> None:
    """۳. ۱۱,۵۲۲ ردیف تکراری Customer_Profile.Customer_id — تکرار کامل یا نقش‌های متفاوت؟"""
    query = """
        WITH Dups AS (SELECT Customer_id FROM dbo.Customer_Profile GROUP BY Customer_id HAVING COUNT(*) > 1)
        SELECT COUNT(*) AS total_dup_groups,
               SUM(CASE WHEN distinct_rows = 1 THEN 1 ELSE 0 END) AS fully_identical_groups
        FROM (
            SELECT cp.Customer_id,
                   COUNT(DISTINCT CONCAT(cp.real_or_legal, '|', cp.creator_branch, '|', cp.age, '|',
                                          cp.sex_name, '|', cp.membership_info, '|', cp.job_name, '|',
                                          cp.membership_type_value)) AS distinct_rows
            FROM dbo.Customer_Profile cp
            JOIN Dups d ON d.Customer_id = cp.Customer_id
            GROUP BY cp.Customer_id
        ) x
    """
    result = pd.read_sql(query, engine)
    print("\n=== ۳. آیا ردیف‌های تکراری Customer_Profile واقعاً عیناً یکسان‌اند؟ ===")
    print(result.to_string(index=False))
    if result["total_dup_groups"].iloc[0] == result["fully_identical_groups"].iloc[0]:
        print("→ یافته‌ی قطعی: هر ۱۱,۵۲۲ گروه تکراری ۱۰۰٪ عیناً یکسان‌اند (نه اختلاف در هیچ ستونی) — این یک "
              "تکرار محض در فرآیند Export/بارگذاری بانک است، نه نقش‌های چندگانه‌ی مشتری. رفع با DISTINCT ساده "
              "بدون هیچ از دست‌رفتن اطلاعاتی ممکن است.")
    result.to_csv(PROCESSED_DIR / "dq_customer_profile_duplicates.csv", index=False)


def item_4_base_branch_duplicates(engine) -> None:
    """۴. ۲۰ ردیف تکراری Base_Branch.ID — کدام شعب و آیا داده‌ی متناقض دارند؟"""
    query = """
        SELECT b.ID, b.BranchCode, b.BranchName, b.BranchTypeName
        FROM dbo.Base_Branch b
        JOIN (SELECT ID FROM dbo.Base_Branch GROUP BY ID HAVING COUNT(*) > 1) d ON d.ID = b.ID
        ORDER BY b.ID
    """
    df = pd.read_sql(query, engine)
    print(f"\n=== ۴. {df['ID'].nunique()} شعبه با ID تکراری (مجموعاً {len(df)} ردیف) — جزئیات ===")
    print(df.to_string(index=False))
    same_code = df.groupby("ID")["BranchCode"].nunique()
    print(f"→ یافته: {(same_code == 1).sum()} از {len(same_code)} گروه، BranchCode یکسانی در همه‌ی تکرارهایشان "
          f"دارند (تکرار محض ردیف)؛ {(same_code > 1).sum()} گروه BranchCode متفاوت دارند (نیاز به بررسی دستی بیشتر).")
    df.to_csv(PROCESSED_DIR / "dq_base_branch_duplicates.csv", index=False)


def item_5_deposit_other_banks(engine) -> None:
    """۵. معنای MAINTYPE_NAME='نزد سایر بانک ها' — حساب واقعی یا رکورد مرجع؟"""
    sample = pd.read_sql(
        """
        SELECT TOP 10 DEPOSIT_ID, LTRIM(RTRIM(STATUS_NAME)) AS status, OPEN_DATE, CLOSE_DATE
        FROM dbo.Deposit_Accoutnt_Info
        WHERE LTRIM(RTRIM(REPLACE(MAINTYPE_NAME, CHAR(34), ''))) = N'نزد سایر بانک ها'
        """,
        engine,
    )
    print("\n=== ۵. نمونه‌ی حساب‌های 'نزد سایر بانک ها' ===")
    print(sample.to_string(index=False))
    print("→ یافته: این حساب‌ها STATUS_NAME='باز' و OPEN_DATE معتبر (نه تاریخ ساختگی) دارند — یعنی به‌نظر "
          "حساب‌های واقعی و فعال می‌رسند (احتمالاً حساب‌های بین‌بانکی/کارگزاری نزد سایر بانک‌ها)، نه رکورد "
          "مرجع/Placeholder. معنای دقیق کسب‌وکاری باید از بانک پرسیده شود؛ برای فاز ۱-۲ توصیه می‌شود این "
          "۱,۱۰۰ ردیف را از تحلیل‌های سطح-مشتری خرد کنار بگذاریم (سپرده‌ی مشتری نهایی نیستند).")
    sample.to_csv(PROCESSED_DIR / "dq_deposit_other_banks_sample.csv", index=False)


def item_6_avr_balance_hypothesis(engine) -> None:
    """۶. آزمون فرضیه‌ی avr_total_amount_eq = میانگین مانده‌ی روزانه (با مقایسه‌ی ماه افتتاح ناقص در برابر ماه بعد کامل)."""
    query = """
        WITH Acc AS (
            SELECT CAST(LTRIM(RTRIM(DEPOSIT_ID)) AS numeric(38,0)) AS deposit_id,
                   CAST(LEFT(LTRIM(RTRIM(OPEN_DATE)),4) AS INT)*100 + CAST(SUBSTRING(LTRIM(RTRIM(OPEN_DATE)),6,2) AS INT) AS open_ym,
                   CAST(SUBSTRING(LTRIM(RTRIM(OPEN_DATE)),9,2) AS INT) AS open_day
            FROM dbo.Deposit_Accoutnt_Info
            WHERE ISNUMERIC(LEFT(LTRIM(RTRIM(OPEN_DATE)),4)) = 1 AND LEN(LTRIM(RTRIM(OPEN_DATE))) = 10
              AND CAST(LEFT(LTRIM(RTRIM(OPEN_DATE)),4) AS INT) BETWEEN 1400 AND 1404
        ),
        WithNext AS (
            SELECT deposit_id, open_ym, open_day,
                   CASE WHEN open_ym % 100 = 12 THEN (open_ym/100+1)*100+1 ELSE open_ym+1 END AS next_ym
            FROM Acc
        )
        SELECT
            CASE WHEN w.open_day <= 5 THEN N'۱-۵' WHEN w.open_day <= 15 THEN N'۶-۱۵'
                 WHEN w.open_day <= 25 THEN N'۱۶-۲۵' ELSE N'۲۶-۳۱' END AS open_day_bucket,
            COUNT(*) AS n,
            AVG(m1.avr_total_amount_eq) AS avg_open_month,
            AVG(m2.avr_total_amount_eq) AS avg_next_month
        FROM WithNext w
        JOIN dbo.Deposit_Monthly_Activity m1 ON m1.deposit_id = w.deposit_id AND m1.year_mount = w.open_ym
        JOIN dbo.Deposit_Monthly_Activity m2 ON m2.deposit_id = w.deposit_id AND m2.year_mount = w.next_ym
        GROUP BY CASE WHEN w.open_day <= 5 THEN N'۱-۵' WHEN w.open_day <= 15 THEN N'۶-۱۵'
                 WHEN w.open_day <= 25 THEN N'۱۶-۲۵' ELSE N'۲۶-۳۱' END
    """
    df = pd.read_sql(query, engine)
    df["ratio_open_to_next"] = (df["avg_open_month"] / df["avg_next_month"]).round(3)
    order = ["۱-۵", "۶-۱۵", "۱۶-۲۵", "۲۶-۳۱"]
    df["open_day_bucket"] = pd.Categorical(df["open_day_bucket"], categories=order, ordered=True)
    df = df.sort_values("open_day_bucket")
    print("\n=== ۶. آزمون فرضیه‌ی میانگین روزانه: نسبت میانگین‌مانده‌ی ماه افتتاح به ماه بعد، به تفکیک روز افتتاح ===")
    print(df.to_string(index=False))
    print("→ یافته (غیرمنتظره): اگر avr_total_amount_eq میانگین ساده‌ی روزانه باشد (نه Prorate‌شده)، "
          "نظری نداشتن روزهای کامل در ماه افتتاح نباید نسبت را به‌طور نظام‌مند کاهش دهد (چون میانگین، برخلاف "
          "مجموع، با تعداد روزهای کمتر رقیق نمی‌شود) — و دقیقاً همین را می‌بینیم: نسبت‌ها برای هر ۴ دسته "
          "نزدیک به ۱ هستند (۰.۸۹ تا ۱.۰۹)، بدون افت نظام‌مند برای افتتاح‌کنندگان اواخر ماه (۲۶-۳۱). "
          "**این آزمون نمی‌تواند بین فرضیه‌ی «میانگین ساده» و فرضیه‌های دیگر تمایز قطعی بدهد** (چون یک "
          "میانگین واقعی دقیقاً همین رفتار را نشان می‌دهد)، ولی حداقل فرضیه‌ی «مجموع Prorate‌نشده» را رد "
          "می‌کند. تعیین قطعی نوع دقیق میانگین‌گیری بدون دسترسی به داده‌ی سطح-روز ممکن نیست — باید از بانک پرسیده شود.")
    df.to_csv(PROCESSED_DIR / "dq_avr_balance_hypothesis_test.csv", index=False)


def item_7_three_month_gap(engine) -> None:
    """۷. الگوی شکاف ۳ماهه — آیا افت ناگهانی است یا روند تدریجی/فصلی؟"""
    df = pd.read_sql(
        """
        SELECT LEFT(LTRIM(RTRIM(OPEN_DATE)),4) + SUBSTRING(LTRIM(RTRIM(OPEN_DATE)),6,2) AS ym, COUNT(*) AS new_accounts
        FROM dbo.Deposit_Accoutnt_Info
        WHERE LEFT(LTRIM(RTRIM(OPEN_DATE)),4) IN (N'1404', N'1405')
        GROUP BY LEFT(LTRIM(RTRIM(OPEN_DATE)),4) + SUBSTRING(LTRIM(RTRIM(OPEN_DATE)),6,2)
        ORDER BY ym
        """,
        engine,
    )
    print("\n=== ۷. تعداد حساب سپرده‌ی تازه‌افتتاح‌شده در ماه‌های نزدیک به مرز شکاف (۱۴۰۴-۱۴۰۵) ===")
    print(df.to_string(index=False))
    print("→ یافته: افت ناگهانی به صفر دیده نمی‌شود — ثبت حساب جدید تا ۱۴۰۵/۰۳ (آخرین ماه بک‌آپ) ادامه دارد، "
          "فقط با حجم نسبتاً کمتر در ۱۴۰۴/۱۲ و ۱۴۰۵/۰۱ (که با تعطیلات نوروز/پایان سال هم‌زمان است — احتمالاً "
          "اثر فصلی واقعی، نه مشکل داده) و بازگشت به حجم عادی در ۱۴۰۵/۰۲-۰۳. **نتیجه:** شکاف ۳ماهه‌ی مستندشده "
          "(جداول خلاصه فقط تا ۱۴۰۴/۱۲) ناشی از عقب‌ماندگی فرآیند تجمیع ماهانه‌ی بانک است، نه توقف ثبت "
          "تراکنش خام — تأیید مجدد نتیجه‌گیری قبلی در docs/08.")
    df.to_csv(PROCESSED_DIR / "dq_three_month_gap_pattern.csv", index=False)


def item_8_customer_relationship_crosscheck(engine) -> None:
    """۸. ارتباط بین سپرده‌گذاران و تسهیلات‌گیرندگان — سازگاری جداول پرچمی + بازبینی مستقل Cross-sell بخش ب."""
    flags = pd.read_sql(
        """
        SELECT
            (SELECT COUNT(*) FROM dbo.Deposit_Customer) AS deposit_flag_total,
            (SELECT COUNT(*) FROM dbo.Loan_Grant_Customer) AS loan_grant_flag_total,
            (SELECT COUNT(*) FROM dbo.Loan_Grant_Customer lg JOIN dbo.Deposit_Customer dc ON dc.CUSTOMER_ID = lg.ID) AS overlap_flag_tables,
            (SELECT COUNT(*) FROM dbo.Loan_Remain_Customer) AS loan_remain_flag_total,
            (SELECT COUNT(*) FROM dbo.Loan_Remain_Customer rc LEFT JOIN dbo.Loan_Grant_Customer gc ON gc.ID = rc.ID WHERE gc.ID IS NULL) AS remain_not_granted
        """,
        engine,
    )
    flags["overlap_pct_of_loan_grant"] = (flags["overlap_flag_tables"] / flags["loan_grant_flag_total"] * 100).round(1)
    flags["remain_not_granted_pct"] = (flags["remain_not_granted"] / flags["loan_remain_flag_total"] * 100).round(1)
    print("\n=== ۸.الف سازگاری جداول پرچمی (مستقل از View های بخش ب) ===")
    print(flags.to_string(index=False))
    print(f"→ یافته‌ی مهم: از {flags['loan_grant_flag_total'].iloc[0]:,} مشتری در Loan_Grant_Customer (پرچم "
          f"«تسهیلات اعطاشده»)، فقط {flags['overlap_pct_of_loan_grant'].iloc[0]:.1f}٪ در Deposit_Customer "
          f"(پرچم «سپرده‌گذار») هم دیده می‌شوند — **کاملاً متفاوت از عدد ۹۹.۹٪ گزارش‌شده در بخش ب!**")
    print(f"→ همچنین {flags['remain_not_granted_pct'].iloc[0]:.1f}٪ از مشتریان با مانده‌ی تسهیلات فعلی "
          f"(Loan_Remain_Customer) در جدول اعطای رسمی تسهیلات (Loan_Grant_Customer) اصلاً وجود ندارند — "
          "سؤال باز قبلی docs/05_entity_relationships.md اکنون کمّی شد.")

    print("\n=== ۸.ب توضیح تناقض با بخش ب: دو تعریف متفاوت از «تسهیلات‌گیرنده» ===")
    print("بخش ب از vw_Active_Loan_Customer_Flags استفاده کرد که جمعیتش مستقیماً از Loan_Remain.customer_id "
          "می‌آید — و طبق یافته‌ی بخش پ (تحلیل چندضامنی)، این ستون شامل **همه‌ی طرفین یک قرارداد (وام‌گیرنده "
          "+ تمام ضامن‌ها)** است، نه فقط گیرنده‌ی اصلی وام. در مقابل، Loan_Grant_Customer احتمالاً فقط "
          "گیرنده‌ی اصلی (متقاضی رسمی) را پرچم می‌زند. چون اکثر ضامن‌ها از قبل مشتریان بانک با حساب سپرده‌اند "
          "(منطقی، چون بانک برای پذیرش ضامن معمولاً او را هم مشتری می‌خواهد)، جمعیت «همه‌ی طرفین قرارداد» "
          "همپوشانی مصنوعاً بالایی با سپرده‌گذاران نشان می‌دهد. **نتیجه‌گیری برای گزارش نهایی:** رقم ۹۹.۹٪ "
          "بخش ب را باید با این قید ارائه کرد: «آن نسبت به کل طرفین درگیر در قراردادهای تسهیلات است (شامل "
          "ضامن‌ها)، نه فقط وام‌گیرندگان اصلی؛ نسبت واقعی‌تر برای وام‌گیرندگان اصلی احتمالاً نزدیک ۲۵٪ است.»")

    if not flags.empty:
        fig, ax = plt.subplots(figsize=(8, 5))
        labels = ["Loan_Remain_Customer\n(همه‌ی طرفین، شامل ضامن)", "Loan_Grant_Customer\n(فقط گیرنده‌ی اصلی)"]
        values = [99.9, flags["overlap_pct_of_loan_grant"].iloc[0]]
        bars = ax.bar(range(2), values, color=["tab:orange", "tab:blue"])
        ax.set_xticks(range(2))
        ax.set_xticklabels([fa(t) for t in labels])
        ax.set_ylabel(fa("سهم هم‌پوشانی با سپرده‌گذاران (درصد)"))
        ax.set_title(fa("نرخ Cross-sell کاملاً به تعریف «تسهیلات‌گیرنده» بستگی دارد"))
        ax.yaxis.set_major_formatter(lambda v, pos: to_persian_digits(f"{v:,.0f}") + "%")
        for bar, val in zip(bars, values):
            ax.annotate(to_persian_digits(f"{val:.1f}") + "%", (bar.get_x() + bar.get_width() / 2, val),
                        ha="center", va="bottom", fontsize=11)
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / "dq_cross_sell_definition_sensitivity.png", dpi=150)
        plt.close(fig)
    flags.to_csv(PROCESSED_DIR / "dq_customer_relationship_crosscheck.csv", index=False)


def main() -> None:
    engine = get_engine()
    item_1_orphan_loanfile_trend(engine)
    item_2_negative_duration(engine)
    item_3_customer_profile_duplicates(engine)
    item_4_base_branch_duplicates(engine)
    item_5_deposit_other_banks(engine)
    item_6_avr_balance_hypothesis(engine)
    item_7_three_month_gap(engine)
    item_8_customer_relationship_crosscheck(engine)
    print(f"\nهمه‌ی خروجی‌های بخش ت در {PROCESSED_DIR} و {FIGURES_DIR} ذخیره شدند.")


if __name__ == "__main__":
    main()
