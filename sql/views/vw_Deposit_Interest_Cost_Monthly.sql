-- هزینه‌ی سود پرداختی به سپرده‌گذاران، به تفکیک شعبه و ماه — ورودی محاسبه‌ی سود و زیان فاز ۱
-- منبع: DepositIDInterest (مبلغ واقعی سود پرداختی هر حساب در هر ماه، از بانک دریافت شد)
--
-- هشدار حل‌نشده (ریشه‌یابی در 2026-08-28، جزئیات در docs/06_phase1_sql_views.md):
-- جدول خام DepositIDInterest حاوی ردیف‌های کاملاً تکراری است (یک حساب تا ۶۳ بار با مقدار عیناً یکسان).
-- این View با DISTINCT این تکرارهای عیناً یکسان را حذف می‌کند (قطعاً درست‌تر از SUM خام)، اما حتی بعد
-- از این حذف، جمع ماهانه هنوز با جدول مرجع بانک (Interset_branch_sum) یکی نمی‌شود (برای اسفند ۱۴۰۴:
-- خام=۱۴.۵۹، پس از DISTINCT=۵.۱۱، جدول بانک=۹.۵۱ هزار میلیارد ریال) — چون این جدول شناسه‌ی تراکنش ندارد
-- و نمی‌توان «تکرار واقعی عیناً یکسان» را از «دو واریز سود جدا با مقدار تصادفاً یکسان» تفکیک کرد.
-- نتیجه: عدد این View را به‌عنوان یک محدوده (۵.۱ تا ۱۴.۶ هزار میلیارد) در نظر بگیرید، نه عدد قطعی؛
-- برای گزارش نهایی فاز ۱، توضیح از بانک درباره‌ی منطق محاسبه‌ی Interset_branch_sum لازم است.
CREATE OR ALTER VIEW dbo.vw_Deposit_Interest_Cost_Monthly AS
SELECT
    year_month,
    branch_code,
    branch_name,
    city_name,
    COUNT(DISTINCT Depositid)   AS account_count,
    SUM(Amount)                 AS total_interest_paid
FROM (
    SELECT DISTINCT
        CAST(LTRIM(RTRIM(REPLACE(REPLACE(di.Year_Mounth, CHAR(13), ''), CHAR(10), ''))) AS int) AS year_month,
        b.branch_code,
        b.branch_name,
        b.city_name,
        di.Depositid,
        di.Amount
    FROM dbo.DepositIDInterest di
    LEFT JOIN dbo.vw_Branch_Dim b
        ON REPLACE(LTRIM(RTRIM(di.BranchCode)), CHAR(13), '') = b.branch_code
) dedup
GROUP BY year_month, branch_code, branch_name, city_name;
