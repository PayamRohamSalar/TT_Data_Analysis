"""
فاز ۱ — بخش «ب: تحلیل‌های ترکیبی» از فهرست پیشنهادی تحلیل‌ها (docs/11_table_analysis_opportunities.md،
docs/EXECUTION_LOG.md ۲۰۲۶-۰۹-۰۳)، نیازمند Join چند جدول:

۱. نسبت Cross-sell: چند درصد مشتریان هم سپرده‌گذار و هم تسهیلات‌گیرنده‌اند
۲. نرخ سود مؤثر واقعی تسهیلات (به تفکیک نوع) در برابر نرخ سود مؤثر برآوردی سپرده (به تفکیک نوع) — حاشیه‌ی سود
۳. نسبت پوشش وثیقه (USED_COST/GRANT_AMOUNT) به تفکیک نوع تسهیلات و بخش اقتصادی
۴. تحلیل عمیق بخش «اعتباراسنادی» (اولویت بالا) — روند ۶۰ماهه‌ی مانده/NPL در برابر سایر بخش‌ها
۵. کوهورت افتتاح حساب سپرده (۱۳۹۹-۱۴۰۴) و نرخ ماندگاری در اسفند ۱۴۰۴
۶. Vintage Analysis تسهیلات: کیفیت پرتفوی (نسبت NPL) به تفکیک سال اعطا

⚠️ نکات مهمی که باید رعایت شوند (تجربه‌ی این پروژه):
- هرگز مستقیم روی Loan_Remain/Loan_Contract_Info خام SUM/COUNT نزنید — از vw_Loan_Contract_Dedup و
  الگوی ROW_NUMBER مشابه vw_Loan_Remain_By_Branch_Month استفاده کنید.
- ستون‌های year_mount/year_month/Transaction_Date/Year_Mounth عددی‌اند؛ تقسیم بدون CAST به bigint
  نتیجه‌ی اعشاری می‌دهد.
- LOAN_INTEREST_RATE/LOAN_PREFERED_RATE در Loan_Contract_Info از نوع nvarchar ذخیره شده‌اند (ولی ۱۰۰٪
  مقادیرشان عددی است، تأیید شد با ISNUMERIC) — قبل از محاسبه باید صریحاً CAST(... AS float) شوند.
- نرخ سود مؤثر سپرده در این تحلیل یک **برآورد پرتفویی** است (مجموع سود واقعی پرداختی ۱۲ ماه اخیر
  تقسیم بر مجموع مانده‌ی میانگین همان ۱۲ ماه)، نه نرخ اسمی مصوب — چون هیچ ستون «نرخ سود مصوب» در
  دیتابیس وجود ندارد (طبق docs/04_data_gap_resolution_report.md، بانک به‌جای نرخ، مبلغ واقعی پرداختی
  را داد). حاشیه‌ی سود حاصل از مقایسه‌ی این برآورد با نرخ قراردادی تسهیلات باید با همین قید خوانده شود.
- هیچ جدولی مانده‌ی سپرده را مستقیم به شعبه وصل نمی‌کند؛ در این اسکریپت به آن نیازی نبود (بر خلاف ۰۴).

خروجی: نمودار PNG برای هر تحلیل در reports/figures/phase1_market_overview/ و جدول CSV در
data/processed/phase1_market_overview/
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
LAST_12M_START = 140401     # فروردین ۱۴۰۴ — شروع ۱۲ ماه اخیرِ کامل، برای نرخ سود مؤثر سپرده

LOAN_TYPE_CASE_SQL = """
    CASE
        WHEN {col} LIKE N'%قرض الحسنه%'    THEN N'قرض‌الحسنه'
        WHEN {col} LIKE N'%مرابحه%'        THEN N'مرابحه'
        WHEN {col} LIKE N'%مشارکت مدني%'   THEN N'مشارکت مدنی'
        WHEN {col} LIKE N'%فروش اقساطي%'   THEN N'فروش اقساطی'
        WHEN {col} LIKE N'%جعاله%'         THEN N'جعاله'
        WHEN {col} LIKE N'%مضاربه%'        THEN N'مضاربه'
        WHEN {col} LIKE N'%استصناع%'       THEN N'استصناع'
        ELSE N'سایر'
    END
"""


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


def section_1_cross_sell(engine) -> None:
    """۱. نسبت Cross-sell: تقاطع جمعیت vw_Active_Depositor_Flags و vw_Active_Loan_Customer_Flags.

    ⚠️ کارایی (نشست ۲۰۲۶-۰۹-۰۴): vw_Active_Depositor_Flags به‌تنهایی ~۶۰ ثانیه طول می‌کشد (۴ بار
    GROUP BY روی Deposit_Monthly_Activity ۱۱۳ میلیون‌ردیفی داخلش). به‌جای فراخوانی این دو View چند بار
    جدا در SQL (precheck + overlap + cross-tab)، هر دو را فقط یک‌بار کامل به پانداس می‌خوانیم و همه‌ی
    محاسبات (precheck تطابق فضای شناسه + جدول Cross-sell) را در پانداس انجام می‌دهیم.
    """
    depositors = pd.read_sql("SELECT customer_id, is_active_depositor FROM dbo.vw_Active_Depositor_Flags", engine)
    loan_customers = pd.read_sql("SELECT customer_id, is_active_loan_customer FROM dbo.vw_Active_Loan_Customer_Flags", engine)

    # پیش‌بررسی: صحت تطابق فضای شناسه‌ی مشترک قبل از Join اصلی (هر دو View از فضای CustomerHub
    # می‌آیند، طبق docs/05_entity_relationships.md، ولی از دو جدول پایه‌ی متفاوت مشتق شده‌اند).
    depositor_population = len(depositors)
    loan_population = len(loan_customers)
    raw_overlap = depositors["customer_id"].isin(loan_customers["customer_id"]).sum()
    precheck = pd.DataFrame([{
        "depositor_population": depositor_population,
        "loan_population": loan_population,
        "raw_overlap": raw_overlap,
    }])
    print("\n=== ۱.۰ پیش‌بررسی تطابق فضای شناسه (قبل از Join اصلی) ===")
    print(precheck.to_string(index=False))
    overlap_ratio = raw_overlap / min(depositor_population, loan_population)
    print(f"نسبت تقاطع خام به کوچک‌ترین جمعیت: {overlap_ratio:.1%} — "
          f"{'به‌نظر منطقی می‌رسد (فضای شناسه‌ی سازگار)' if overlap_ratio > 0.10 else '⚠️ غیرمنتظره پایین — نیاز به بررسی بیشتر قبل از ادامه'}")

    merged = depositors.merge(loan_customers, on="customer_id", how="outer")
    is_depositor = merged["is_active_depositor"].notna()
    is_loan = merged["is_active_loan_customer"].notna()
    merged["segment"] = "فقط تسهیلات‌گیرنده"
    merged.loc[is_depositor, "segment"] = "فقط سپرده‌گذار"
    merged.loc[is_depositor & is_loan, "segment"] = "هر دو (سپرده + تسهیلات)"
    merged["is_active_either"] = (merged["is_active_depositor"].fillna(0) == 1) | (merged["is_active_loan_customer"].fillna(0) == 1)

    df = (
        merged.groupby("segment", as_index=False)
        .agg(customer_count=("customer_id", "size"), active_count=("is_active_either", "sum"))
        .sort_values("customer_count", ascending=False)
        .reset_index(drop=True)
    )
    df["share_pct"] = (df["customer_count"] / df["customer_count"].sum() * 100).round(2)
    print("\n=== ۱. نسبت Cross-sell (سپرده‌گذار در برابر تسهیلات‌گیرنده، کل جمعیت هر دو View) ===")
    print(df.to_string(index=False))
    both_pct = df.loc[df["segment"].str.contains("هر دو"), "share_pct"]
    if not both_pct.empty:
        print(f"→ {both_pct.iloc[0]:.1f}٪ از کل مشتریانی که در این دو View دیده می‌شوند، هم‌زمان سپرده‌گذار و تسهیلات‌گیرنده‌اند.")

    if not df.empty:
        fig, ax = plt.subplots(figsize=(7, 6))
        ax.pie(df["customer_count"], labels=[fa(s) for s in df["segment"]],
               autopct=lambda p: to_persian_digits(f"{p:.1f}") + "%", textprops={"fontsize": 10})
        ax.set_title(fa("ترکیب مشتریان: فقط سپرده، فقط تسهیلات، یا هر دو (Cross-sell)"))
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / "cross_sell_ratio.png", dpi=150)
        plt.close(fig)
    df.to_csv(PROCESSED_DIR / "cross_sell_ratio.csv", index=False)


def section_2_effective_rate_margin(engine) -> None:
    """۲. نرخ سود مؤثر تسهیلات (قراردادی، وزن‌دهی‌شده بر اساس مبلغ) در برابر نرخ هزینه‌ی سپرده، به تفکیک
    نوع محصول — حاشیه‌ی سود تقریبی بانک.

    ⚠️ رفع باگ روش‌شناختی (بازبینی مستقل Claude Opus، ۲۰۲۶-۰۹-۱۱، بند ۲.۴): نسخه‌ی اول این تابع نرخ سود
    «مؤثر» سپرده را با INNER JOIN به DepositIDInterest محاسبه می‌کرد — یعنی هم صورت (سود پرداختی) و هم
    مخرج (مانده‌ی میانگین) فقط شامل حساب‌هایی بود که سود گرفته‌اند (~۳۷٪ کل حساب‌ها، طبق docs/04). حساب‌های
    قرض‌الحسنه/جاری (بیش از نیمی از منابع بانک) کاملاً از مخرج حذف می‌شدند، پس نرخ به‌طور مصنوعی بالا
    می‌رفت (۲۸.۶۴٪) و حاشیه‌ی سود منفی کاذب (-۱۰.۵۵ واحد درصد) نتیجه می‌داد. این مقایسه‌ی نرخ قراردادیِ
    «همه‌ی وام‌ها» با نرخ واقعیِ «فقط زیرمجموعه‌ی سود‌ده‌ی سپرده» از پایه هم‌سنخ نبود.
    رفع: علاوه بر شکست به تفکیک نوع (که همچنان فقط برای حساب‌های سود‌ده معنادار است و صریحاً همین‌طور
    برچسب خورده)، یک «نرخ هزینه‌ی کل تأمین مالی» جدید محاسبه شد: کل سود پرداختی ۱۲ ماه اخیر ÷ میانگین
    مانده‌ی **کل** سپرده (همه‌ی حساب‌ها، نه فقط سود‌ده) در همان ۱۲ ماه — این عدد است که باید در برابر نرخ
    تسهیلات مقایسه شود، نه نرخ زیرمجموعه‌ی سود‌ده."""
    loan_case = LOAN_TYPE_CASE_SQL.format(col="loan_type_description")
    loan_query = f"""
        SELECT
            {loan_case} AS loan_type_group,
            COUNT(*) AS loan_count,
            SUM(grant_amount) AS total_granted,
            SUM((CAST(loan_interest_rate AS float) + ISNULL(CAST(loan_prefered_rate AS float),0)) * grant_amount)
                / NULLIF(SUM(grant_amount),0) AS effective_rate_pct
        FROM dbo.vw_Loan_Contract_Dedup
        WHERE grant_amount > 0 AND loan_interest_rate IS NOT NULL
        GROUP BY {loan_case}
        ORDER BY effective_rate_pct DESC
    """
    loan_df = pd.read_sql(loan_query, engine)
    print("\n=== ۲.الف نرخ سود مؤثر قراردادی تسهیلات، وزن‌دهی‌شده بر اساس مبلغ اعطایی (به تفکیک نوع) ===")
    print(loan_df.to_string(index=False))
    if not loan_df.empty:
        save_barh(loan_df.sort_values("effective_rate_pct"), "loan_type_group", "effective_rate_pct",
                   "نرخ سود مؤثر قراردادی تسهیلات به تفکیک نوع (وزن‌دهی‌شده بر مبلغ)",
                   "نرخ سود مؤثر (درصد)", "effective_rate_loan_by_type.png")
    loan_df.to_csv(PROCESSED_DIR / "effective_rate_loan_by_type.csv", index=False)

    # ⚠️ برآورد پرتفویی: مجموع سود واقعی پرداختی ۱۲ ماه اخیر (فروردین تا اسفند ۱۴۰۴) تقسیم بر مجموع
    # مانده‌ی میانگین همان ۱۲ ماه — نه نرخ اسمی مصوب (که در دیتابیس موجود نیست).
    deposit_query = f"""
        WITH InterestByAccount AS (
            SELECT CAST(REPLACE(REPLACE(LTRIM(RTRIM(Depositid)),CHAR(13),''),CHAR(10),'') AS numeric(38,0)) AS deposit_id,
                   SUM(Amount) AS interest_paid_12m
            FROM dbo.DepositIDInterest
            WHERE CAST(REPLACE(REPLACE(Year_Mounth,CHAR(13),''),CHAR(10),'') AS bigint) BETWEEN {LAST_12M_START} AND {LATEST_MONTH}
            GROUP BY CAST(REPLACE(REPLACE(LTRIM(RTRIM(Depositid)),CHAR(13),''),CHAR(10),'') AS numeric(38,0))
        ),
        BalanceByAccount AS (
            SELECT deposit_id, AVG(avr_total_amount_eq) AS avg_balance_12m
            FROM dbo.Deposit_Monthly_Activity
            WHERE CAST(year_mount AS bigint) BETWEEN {LAST_12M_START} AND {LATEST_MONTH}
            GROUP BY deposit_id
        )
        SELECT
            ISNULL(dad.deposit_type, N'نامشخص') AS deposit_type,
            COUNT(*) AS account_count,
            SUM(ib.interest_paid_12m) AS total_interest_12m,
            SUM(bb.avg_balance_12m) AS total_avg_balance_12m,
            SUM(ib.interest_paid_12m) / NULLIF(SUM(bb.avg_balance_12m),0) * 100 AS effective_rate_pct
        FROM InterestByAccount ib
        JOIN BalanceByAccount bb ON bb.deposit_id = ib.deposit_id
        LEFT JOIN dbo.vw_Deposit_Account_Dedup dad ON dad.deposit_id = ib.deposit_id
        WHERE bb.avg_balance_12m > 0
        GROUP BY ISNULL(dad.deposit_type, N'نامشخص')
        ORDER BY effective_rate_pct DESC
    """
    deposit_df = pd.read_sql(deposit_query, engine)
    print("\n=== ۲.ب نرخ سود مؤثر سپرده، فقط میان حساب‌های سود‌ده (۱۲ ماه اخیر) به تفکیک نوع — NOT نرخ کل منابع ===")
    print(deposit_df.to_string(index=False))
    if not deposit_df.empty:
        save_barh(deposit_df.sort_values("effective_rate_pct"), "deposit_type", "effective_rate_pct",
                   "نرخ سود مؤثر سپرده، فقط میان حساب‌های سود‌ده به تفکیک نوع (۱۲ ماه اخیر)",
                   "نرخ سود مؤثر در زیرمجموعه‌ی سود‌ده (درصد سالانه)", "effective_rate_deposit_by_type.png")
    deposit_df.to_csv(PROCESSED_DIR / "effective_rate_deposit_by_type.csv", index=False)

    # نرخ هزینه‌ی کل تأمین مالی: صورت = کل سود پرداختی (همان جمعیت سود‌ده)، مخرج = میانگین مانده‌ی
    # ماهانه‌ی کل سپرده (همه‌ی حساب‌ها، شامل قرض‌الحسنه/جاری) — تنها مبنای هم‌سنخ با نرخ تسهیلات.
    total_deposit_base_query = f"""
        SELECT AVG(monthly_total) AS avg_total_deposit_base_12m
        FROM (
            SELECT year_mount, SUM(avr_total_amount_eq) AS monthly_total
            FROM dbo.Deposit_Monthly_Activity
            WHERE CAST(year_mount AS bigint) BETWEEN {LAST_12M_START} AND {LATEST_MONTH}
            GROUP BY year_mount
        ) monthly
    """
    total_base = pd.read_sql(total_deposit_base_query, engine)["avg_total_deposit_base_12m"].iloc[0]
    total_interest_bearing_only = deposit_df["total_interest_12m"].sum()

    overall_loan_rate = (
        (loan_df["effective_rate_pct"] * loan_df["total_granted"]).sum() / loan_df["total_granted"].sum()
        if not loan_df.empty else float("nan")
    )
    interest_bearing_only_rate = (
        total_interest_bearing_only / deposit_df["total_avg_balance_12m"].sum() * 100
        if not deposit_df.empty else float("nan")
    )
    cost_of_funds_rate = total_interest_bearing_only / total_base * 100 if total_base else float("nan")

    print(f"\n→ نرخ سود مؤثر قراردادی کلی تسهیلات (وزن‌دهی‌شده، همه‌ی وام‌ها): {overall_loan_rate:.2f}٪")
    print(f"→ نرخ سود مؤثر سپرده، فقط زیرمجموعه‌ی سود‌ده (~۳۷٪ حساب‌ها): {interest_bearing_only_rate:.2f}٪ "
          f"⚠️ این عدد را مستقیماً با نرخ تسهیلات مقایسه نکنید — پایه‌ی متفاوتی دارد.")
    print(f"→ نرخ هزینه‌ی کل تأمین مالی (سود پرداختی ÷ میانگین مانده‌ی کل سپرده، همه‌ی حساب‌ها): {cost_of_funds_rate:.2f}٪ "
          f"— این مبنای درست برای مقایسه با نرخ تسهیلات است.")
    print(f"→ حاشیه‌ی سود تقریبی بانک (تسهیلات − هزینه‌ی کل تأمین مالی): {overall_loan_rate - cost_of_funds_rate:.2f} واحد درصد "
          f"⚠️ چون DepositIDInterest فقط ~۳۷٪ حساب‌ها را پوشش می‌دهد (طبق docs/04) و با جدول مرجع خودِ بانک "
          f"(Interset_branch_sum) هم تا ~۱.۸۶ برابر اختلاف دارد (طبق docs/06)، صورت این کسر خودش کم‌برآورد "
          f"محتمل است — این حاشیه را کف واقعی (نه عدد نهایی) در نظر بگیرید؛ حاشیه‌ی واقعی به‌احتمال زیاد "
          f"از این هم بزرگ‌تر (مثبت‌تر) است.")
    pd.DataFrame([{
        "overall_loan_rate_pct": overall_loan_rate,
        "deposit_rate_interest_bearing_only_pct": interest_bearing_only_rate,
        "cost_of_funds_rate_all_accounts_pct": cost_of_funds_rate,
        "approx_margin_pct_points_vs_cost_of_funds": overall_loan_rate - cost_of_funds_rate,
    }]).to_csv(PROCESSED_DIR / "effective_rate_margin_summary.csv", index=False)


def section_3_collateral_coverage(engine) -> None:
    """۳. نسبت پوشش وثیقه (USED_COST/GRANT_AMOUNT) به تفکیک نوع تسهیلات و بخش اقتصادی (آخرین ماه)."""
    loan_case = LOAN_TYPE_CASE_SQL.format(col="loan_type_description")
    by_type_query = f"""
        SELECT
            {loan_case} AS loan_type_group,
            COUNT(*) AS loan_count,
            SUM(grant_amount) AS total_granted,
            SUM(used_cost) AS total_collateral,
            SUM(used_cost) * 100.0 / NULLIF(SUM(grant_amount),0) AS coverage_pct
        FROM dbo.vw_Loan_Contract_Dedup
        WHERE grant_amount > 0 AND used_cost IS NOT NULL
        GROUP BY {loan_case}
        ORDER BY coverage_pct DESC
    """
    by_type = pd.read_sql(by_type_query, engine)
    print("\n=== ۳.الف نسبت پوشش وثیقه (USED_COST/GRANT_AMOUNT) به تفکیک نوع تسهیلات ===")
    print(by_type.to_string(index=False))
    if not by_type.empty:
        save_barh(by_type.sort_values("coverage_pct"), "loan_type_group", "coverage_pct",
                   "نسبت پوشش وثیقه به تفکیک نوع تسهیلات",
                   "پوشش وثیقه (درصد از مبلغ اعطایی)", "collateral_coverage_by_loan_type.png")
    by_type.to_csv(PROCESSED_DIR / "collateral_coverage_by_loan_type.csv", index=False)

    by_sector_query = f"""
        WITH LatestSector AS (
            SELECT loanfile_id, LTRIM(RTRIM(REPLACE(ECO_SEC, CHAR(34), ''))) AS economic_sector,
                   ROW_NUMBER() OVER (PARTITION BY loanfile_id ORDER BY customer_id) AS rn
            FROM dbo.Loan_Remain
            WHERE Transaction_Date = {LATEST_LOAN_TD}
        )
        SELECT
            s.economic_sector,
            COUNT(DISTINCT c.loanfile_id) AS loan_count,
            SUM(c.grant_amount) AS total_granted,
            SUM(c.used_cost) AS total_collateral,
            SUM(c.used_cost) * 100.0 / NULLIF(SUM(c.grant_amount),0) AS coverage_pct
        FROM LatestSector s
        JOIN dbo.vw_Loan_Contract_Dedup c ON c.loanfile_id = s.loanfile_id
        WHERE s.rn = 1 AND c.grant_amount > 0 AND c.used_cost IS NOT NULL
        GROUP BY s.economic_sector
        ORDER BY coverage_pct DESC
    """
    by_sector = pd.read_sql(by_sector_query, engine)
    print("\n=== ۳.ب نسبت پوشش وثیقه به تفکیک بخش اقتصادی (بر اساس ECO_SEC آخرین ماه) ===")
    print(by_sector.to_string(index=False))
    if not by_sector.empty:
        save_barh(by_sector.sort_values("coverage_pct"), "economic_sector", "coverage_pct",
                   "نسبت پوشش وثیقه به تفکیک بخش اقتصادی (آخرین ماه)",
                   "پوشش وثیقه (درصد از مبلغ اعطایی)", "collateral_coverage_by_sector.png")
    by_sector.to_csv(PROCESSED_DIR / "collateral_coverage_by_sector.csv", index=False)


def section_4_letters_of_credit_deep_dive(engine) -> None:
    """۴. تحلیل عمیق بخش «اعتباراسنادی» (اولویت بالا) — روند ۶۰ماهه‌ی مانده/NPL در برابر سایر بخش‌ها،
    و ترکیب نوع تسهیلات این بخش.

    ⚠️ کارایی (نشست ۲۰۲۶-۰۹-۰۴): کوئری GROUP BY year_month بدون فیلتر مستقیم روی
    vw_Loan_Remain_By_Branch_Month (که داخلش ROW_NUMBER روی کل ۷۰ میلیون ردیف Loan_Remain بدون فیلتر
    اجرا می‌شود) حتی بعد از ساخت ایندکس پوششی و حتی با MAXDOP 1 باز هم Timeout می‌داد (پلن غیرقابل‌اتکا،
    گیر در CXSYNC_PORT). راه‌حل: دقیقاً همان الگوی «قطعه‌قطعه ماهانه» که برای vw_Deposit_Portfolio_Monthly
    جواب داد — حلقه‌ی پایتون روی هر یک از ۶۰ ماه، هر بار یک کوئری فیلترشده و سبک (~۱۲ ثانیه با ایندکس
    جدید) روی خودِ Loan_Remain (بدون نیاز به Join شعبه، چون این بخش فقط بخش اقتصادی می‌خواهد نه شعبه).
    """
    months = pd.read_sql("SELECT DISTINCT Transaction_Date FROM dbo.Loan_Remain ORDER BY Transaction_Date", engine)[
        "Transaction_Date"
    ].tolist()
    print(f"در حال محاسبه‌ی روند ماهانه به‌صورت قطعه‌قطعه ({len(months)} ماه، ممکن است چند دقیقه طول بکشد)...")
    monthly_rows = []
    for i, td in enumerate(months):
        month_query = f"""
            WITH OnePerLoanMonth AS (
                SELECT loanfile_id, LTRIM(RTRIM(REPLACE(ECO_SEC, CHAR(34), ''))) AS sector, MANDE_JARI, Total_Remain,
                       ROW_NUMBER() OVER (PARTITION BY loanfile_id ORDER BY customer_id) AS rn
                FROM dbo.Loan_Remain
                WHERE Transaction_Date = {td}
            )
            SELECT
                SUM(CASE WHEN sector = N'اعتباراسنادی' THEN Total_Remain ELSE 0 END) AS loc_balance,
                SUM(CASE WHEN sector = N'اعتباراسنادی' THEN Total_Remain - MANDE_JARI ELSE 0 END) AS loc_npl,
                SUM(CASE WHEN sector <> N'اعتباراسنادی' OR sector IS NULL THEN Total_Remain ELSE 0 END) AS other_balance,
                SUM(CASE WHEN sector <> N'اعتباراسنادی' OR sector IS NULL THEN Total_Remain - MANDE_JARI ELSE 0 END) AS other_npl
            FROM OnePerLoanMonth
            WHERE rn = 1
        """
        row = pd.read_sql(month_query, engine).iloc[0].to_dict()
        row["year_month"] = int(td) // 100
        monthly_rows.append(row)
        if (i + 1) % 12 == 0:
            print(f"  {i + 1}/{len(months)} ماه پردازش شد...")
    trend = pd.DataFrame(monthly_rows)[["year_month", "loc_balance", "loc_npl", "other_balance", "other_npl"]]
    trend["loc_npl_ratio_pct"] = (trend["loc_npl"] / trend["loc_balance"] * 100).round(1)
    trend["other_npl_ratio_pct"] = (trend["other_npl"] / trend["other_balance"] * 100).round(1)
    print("\n=== ۴.الف روند ۶۰ماهه‌ی نسبت NPL بخش «اعتباراسنادی» در برابر میانگین سایر بخش‌ها (۵ ماه اول/آخر) ===")
    print(pd.concat([trend.head(), trend.tail()])[
        ["year_month", "loc_balance", "loc_npl_ratio_pct", "other_npl_ratio_pct"]
    ].to_string(index=False))

    if not trend.empty:
        fig, ax = plt.subplots(figsize=(12, 5))
        x_pos = range(len(trend))
        x_labels = [to_persian_digits(v) for v in trend["year_month"].astype(int).astype(str)]
        ax.plot(list(x_pos), trend["loc_npl_ratio_pct"], label=fa("اعتباراسنادی"), linewidth=2)
        ax.plot(list(x_pos), trend["other_npl_ratio_pct"], label=fa("میانگین سایر بخش‌ها"), linewidth=2, linestyle="--")
        ax.set_xticks(list(x_pos)[::4])
        ax.set_xticklabels(x_labels[::4], rotation=90, fontsize=6)
        ax.set_title(fa("نسبت مطالبات غیرجاری (NPL) بخش اعتباراسنادی در برابر سایر بخش‌ها — روند ۶۰ماهه"))
        ax.set_xlabel(fa("ماه (شمسی YYYYMM)"))
        ax.set_ylabel(fa("درصد"))
        ax.yaxis.set_major_formatter(lambda v, pos: to_persian_digits(f"{v:,.0f}") + "%")
        ax.legend(prop={"family": "Vazirmatn"})
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / "letters_of_credit_npl_trend.png", dpi=150)
        plt.close(fig)
    trend.to_csv(PROCESSED_DIR / "letters_of_credit_npl_trend.csv", index=False)

    composition_query = f"""
        WITH LatestSector AS (
            SELECT loanfile_id, LTRIM(RTRIM(REPLACE(ECO_SEC, CHAR(34), ''))) AS economic_sector,
                   ROW_NUMBER() OVER (PARTITION BY loanfile_id ORDER BY customer_id) AS rn
            FROM dbo.Loan_Remain
            WHERE Transaction_Date = {LATEST_LOAN_TD}
        )
        SELECT
            {LOAN_TYPE_CASE_SQL.format(col="c.loan_type_description")} AS loan_type_group,
            COUNT(DISTINCT c.loanfile_id) AS loan_count,
            SUM(c.grant_amount) AS total_granted
        FROM LatestSector s
        JOIN dbo.vw_Loan_Contract_Dedup c ON c.loanfile_id = s.loanfile_id
        WHERE s.rn = 1 AND s.economic_sector = N'اعتباراسنادی'
        GROUP BY {LOAN_TYPE_CASE_SQL.format(col="c.loan_type_description")}
        ORDER BY total_granted DESC
    """
    composition = pd.read_sql(composition_query, engine)
    print("\n=== ۴.ب ترکیب نوع تسهیلات در بخش «اعتباراسنادی» (آخرین ماه) — منشأ ریسک از کدام نوع می‌آید؟ ===")
    print(composition.to_string(index=False))
    if not composition.empty:
        save_barh(composition, "loan_type_group", "total_granted",
                   "ترکیب نوع تسهیلات در بخش اعتباراسنادی (بر اساس مبلغ اعطایی)",
                   "مبلغ اعطایی (ریال)", "letters_of_credit_type_composition.png")
    composition.to_csv(PROCESSED_DIR / "letters_of_credit_type_composition.csv", index=False)


def section_5_deposit_cohort_retention(engine) -> None:
    """۵. کوهورت افتتاح حساب سپرده (سال اولین حساب هر مشتری، ۱۳۹۹-۱۴۰۴) و نرخ ماندگاری در اسفند ۱۴۰۴
    (طبق تعریف vw_Active_Depositor_Flags)."""
    query = """
        WITH CustomerFirstOpen AS (
            SELECT
                CAST(LTRIM(RTRIM(MAIN_CUSTOMER_ID)) AS numeric(38,0)) AS customer_id,
                LEFT(MIN(LTRIM(RTRIM(OPEN_DATE))), 4) AS cohort_year
            FROM dbo.Deposit_Accoutnt_Info
            WHERE ISNUMERIC(LTRIM(RTRIM(MAIN_CUSTOMER_ID))) = 1
              AND LEN(LTRIM(RTRIM(OPEN_DATE))) = 10
            GROUP BY LTRIM(RTRIM(MAIN_CUSTOMER_ID))
        )
        SELECT
            c.cohort_year,
            COUNT(*) AS cohort_size,
            SUM(ISNULL(af.is_active_depositor,0)) AS still_active_140412,
            SUM(ISNULL(af.is_active_depositor,0)) * 100.0 / COUNT(*) AS retention_pct
        FROM CustomerFirstOpen c
        LEFT JOIN dbo.vw_Active_Depositor_Flags af ON af.customer_id = c.customer_id
        WHERE c.cohort_year BETWEEN '1399' AND '1404'
        GROUP BY c.cohort_year
        ORDER BY c.cohort_year
    """
    df = pd.read_sql(query, engine)
    print("\n=== ۵. کوهورت افتتاح حساب سپرده (سال اولین حساب مشتری) و نرخ ماندگاری در اسفند ۱۴۰۴ ===")
    print(df.to_string(index=False))
    print("⚠️ توجه: کوهورت‌های جدیدتر (مثلاً ۱۴۰۴) طبیعتاً نرخ ماندگاری بالاتری نشان می‌دهند چون معیار "
          "Tenure در vw_Active_Depositor_Flags (حداقل ۱۲ ماه قدمت) مشتریان بسیار تازه را از ابتدا حذف می‌کند؛ "
          "این یک اثر تعریفی است، نه لزوماً وفاداری بالاتر کوهورت جدید.")

    if not df.empty:
        fig, ax = plt.subplots(figsize=(9, 5))
        x_pos = range(len(df))
        x_labels = [to_persian_digits(y) for y in df["cohort_year"]]
        ax.bar(list(x_pos), df["retention_pct"])
        ax.set_xticks(list(x_pos))
        ax.set_xticklabels(x_labels)
        ax.set_xlabel(fa("سال افتتاح اولین حساب سپرده (کوهورت)"))
        ax.set_ylabel(fa("درصد فعال در اسفند ۱۴۰۴"))
        ax.set_title(fa("نرخ ماندگاری کوهورت‌های افتتاح حساب سپرده تا اسفند ۱۴۰۴"))
        ax.yaxis.set_major_formatter(lambda v, pos: to_persian_digits(f"{v:,.0f}") + "%")
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / "deposit_cohort_retention.png", dpi=150)
        plt.close(fig)
    df.to_csv(PROCESSED_DIR / "deposit_cohort_retention.csv", index=False)


def section_6_loan_vintage_analysis(engine) -> None:
    """۶. Vintage Analysis تسهیلات: کیفیت پرتفوی فعلی (نسبت NPL) بر اساس سال اعطای قرارداد."""
    query = f"""
        WITH LatestRemain AS (
            SELECT loanfile_id, Total_Remain, MANDE_JARI,
                   ROW_NUMBER() OVER (PARTITION BY loanfile_id ORDER BY customer_id) AS rn
            FROM dbo.Loan_Remain
            WHERE Transaction_Date = {LATEST_LOAN_TD}
        )
        SELECT
            LEFT(c.grant_date, 4) AS grant_year,
            COUNT(DISTINCT lr.loanfile_id) AS loan_count,
            SUM(lr.Total_Remain) AS total_balance,
            SUM(lr.Total_Remain - lr.MANDE_JARI) AS npl_balance,
            (SUM(lr.Total_Remain - lr.MANDE_JARI)) * 100.0 / NULLIF(SUM(lr.Total_Remain),0) AS npl_ratio_pct
        FROM LatestRemain lr
        JOIN dbo.vw_Loan_Contract_Dedup c ON c.loanfile_id = lr.loanfile_id
        WHERE lr.rn = 1 AND lr.Total_Remain > 0 AND LEN(c.grant_date) = 10
        GROUP BY LEFT(c.grant_date, 4)
        ORDER BY grant_year
    """
    df = pd.read_sql(query, engine)
    print("\n=== ۶. Vintage Analysis — نسبت NPL مانده‌ی فعلی (اسفند ۱۴۰۴) به تفکیک سال اعطای قرارداد ===")
    print(df.to_string(index=False))
    if not df.empty:
        worst = df.loc[df["npl_ratio_pct"].idxmax()]
        print(f"→ بدترین کیفیت پرتفوی مربوط به قراردادهای اعطاشده در سال {to_persian_digits(worst['grant_year'])} "
              f"است (نسبت NPL: {worst['npl_ratio_pct']:.1f}٪).")

    if not df.empty:
        fig, ax = plt.subplots(figsize=(9, 5))
        x_pos = range(len(df))
        x_labels = [to_persian_digits(y) for y in df["grant_year"]]
        ax.bar(list(x_pos), df["npl_ratio_pct"])
        ax.set_xticks(list(x_pos))
        ax.set_xticklabels(x_labels)
        ax.set_xlabel(fa("سال اعطای قرارداد"))
        ax.set_ylabel(fa("نسبت NPL مانده‌ی فعلی (درصد)"))
        ax.set_title(fa("Vintage Analysis: کیفیت پرتفوی فعلی تسهیلات به تفکیک سال اعطا"))
        ax.yaxis.set_major_formatter(lambda v, pos: to_persian_digits(f"{v:,.0f}") + "%")
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / "loan_vintage_analysis.png", dpi=150)
        plt.close(fig)
    df.to_csv(PROCESSED_DIR / "loan_vintage_analysis.csv", index=False)


def main() -> None:
    engine = get_engine()
    section_1_cross_sell(engine)
    section_2_effective_rate_margin(engine)
    section_3_collateral_coverage(engine)
    section_4_letters_of_credit_deep_dive(engine)
    section_5_deposit_cohort_retention(engine)
    section_6_loan_vintage_analysis(engine)
    print(f"\nهمه‌ی خروجی‌های بخش ب در {PROCESSED_DIR} و {FIGURES_DIR} ذخیره شدند.")


if __name__ == "__main__":
    main()
