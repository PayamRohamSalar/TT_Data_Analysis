-- مانده و طبقه‌بندی مطالبات تسهیلات، به تفکیک شعبه/شهر/بخش اقتصادی/ماه
-- منبع فاز ۱ (بخش «مطالبات بانکی») و فاز ۳ (تفکیک جغرافیایی/بخش اقتصادی)
-- وابسته به vw_Loan_Branch_Map (نگاشت یک‌به‌یک، تکرارها حذف‌شده) و vw_Branch_Dim
--
-- 🐛 باگ حیاتی رفع‌شده (نشست Claude Code بومی، 2026-08-30) — جزئیات کامل در docs/08_data_landscape_report.md:
-- کلید طبیعی واقعی Loan_Remain برابر (loanfile_id, customer_id, Transaction_Date) است، نه
-- (loanfile_id, Transaction_Date) تنها — یک قرارداد می‌تواند چند مشتری (ضامن/شریک) مرتبط داشته باشد،
-- و مانده (Total_Remain و همه‌ی ستون‌های دیگر) عیناً در ردیف هر ضامن تکرار می‌شود (تأیید شد با نمونه‌ی
-- واقعی: یک وام با ۱۳ ضامن، مانده‌ی ۵۲.۵ میلیارد ریالی در هر ۱۳ ردیف). نسخه‌ی قبلی این View مستقیماً
-- SUM(Total_Remain) می‌زد که باعث می‌شد ~۲۸٪ از رکوردهای غیرصفر (وام‌های چندضامنی) چند بار شمرده شوند —
-- SUM کل برای اسفند ۱۴۰۴ به‌اشتباه ۱,۹۶۱ هزار میلیارد ریال بود، در حالی‌که عدد درست ۱,۲۸۲ هزار میلیارد
-- ریال است (~۵۳٪ تورم کاذب). راه‌حل: قبل از تجمیع، دقیقاً یک ردیف به‌ازای هر (loanfile_id, ماه) با
-- ROW_NUMBER (بر مبنای customer_id، صرفاً برای قطعیت انتخاب) نگه داشته می‌شود.
CREATE OR ALTER VIEW dbo.vw_Loan_Remain_By_Branch_Month AS
WITH OnePerLoanMonth AS (
    SELECT
        loanfile_id,
        Transaction_Date,
        ECO_SEC,
        MANDE_JARI,
        Overusance_Remain,
        Postponed_Remain,
        Doubtful_Remain,
        Total_Remain,
        ROW_NUMBER() OVER (PARTITION BY loanfile_id, Transaction_Date ORDER BY customer_id) AS rn
    FROM dbo.Loan_Remain
)
SELECT
    lr.Transaction_Date,
    CAST(lr.Transaction_Date AS bigint) / 100                  AS year_month,   -- شمسی YYYYMM (تقسیم صحیح؛ numeric/100 اعشاری برمی‌گرداند)
    b.branch_code,
    b.branch_name,
    b.city_name,
    b.is_virtual_branch,
    LTRIM(RTRIM(REPLACE(lr.ECO_SEC, CHAR(34), '')))            AS economic_sector,  -- ECO_SEC خام با کوتیشن احاطه شده: '"خدمات"'
    COUNT(DISTINCT lr.loanfile_id)                             AS loan_count,
    SUM(lr.MANDE_JARI)                                         AS current_balance,
    SUM(lr.Overusance_Remain)                                  AS overusance_balance,
    SUM(lr.Postponed_Remain)                                   AS postponed_balance,
    SUM(lr.Doubtful_Remain)                                    AS doubtful_balance,
    SUM(lr.Total_Remain)                                       AS total_balance,
    SUM(lr.Total_Remain - lr.MANDE_JARI)                       AS total_npl_balance  -- کل مطالبات غیرجاری
FROM OnePerLoanMonth lr
LEFT JOIN dbo.vw_Loan_Branch_Map lbm
    ON lbm.loanfile_id = lr.loanfile_id
LEFT JOIN dbo.vw_Branch_Dim b
    ON b.branch_code = lbm.branch_code
WHERE lr.rn = 1
GROUP BY
    lr.Transaction_Date, b.branch_code, b.branch_name, b.city_name, b.is_virtual_branch, LTRIM(RTRIM(REPLACE(lr.ECO_SEC, CHAR(34), '')));
