-- بررسی گرانولاریتی زمانی ۴ جدول فعالیت/مانده ماهانه — برای docs/08_data_landscape_report.md
SET NOCOUNT ON;
USE Alzahra_Final_DB;

PRINT '=== ۱. Loan_Remain: آیا برای هر (loanfile_id, ماه) یک یا چند Transaction_Date وجود دارد؟ ===';
-- چند loanfile_id نمونه را انتخاب و تعداد Transaction_Date یکتا در هر ماه را می‌شماریم
SELECT TOP 5 loanfile_id, COUNT(DISTINCT Transaction_Date) AS distinct_dates_total,
       MIN(Transaction_Date) AS min_date, MAX(Transaction_Date) AS max_date, COUNT(*) AS row_count
FROM Loan_Remain
GROUP BY loanfile_id
ORDER BY COUNT(*) DESC;

PRINT '--- همان ۵ قرارداد، ولی تفکیک per-month (آیا در یک ماه چند Transaction_Date متفاوت دارند؟) ---';
WITH Top5 AS (
    SELECT TOP 5 loanfile_id FROM Loan_Remain GROUP BY loanfile_id ORDER BY COUNT(*) DESC
)
SELECT lr.loanfile_id, CAST(lr.Transaction_Date AS bigint)/100 AS year_month,
       COUNT(DISTINCT lr.Transaction_Date) AS distinct_dates_in_month, COUNT(*) AS rows_in_month
FROM Loan_Remain lr
JOIN Top5 t ON t.loanfile_id = lr.loanfile_id
GROUP BY lr.loanfile_id, CAST(lr.Transaction_Date AS bigint)/100
ORDER BY lr.loanfile_id, year_month;

PRINT '=== ۲. توزیع کلی: چند Transaction_Date یکتا در کل جدول وجود دارد، و فاصله‌ی متوسط؟ ===';
SELECT COUNT(DISTINCT Transaction_Date) AS distinct_dates_overall,
       MIN(Transaction_Date) AS min_date, MAX(Transaction_Date) AS max_date
FROM Loan_Remain;

PRINT '--- همه‌ی Transaction_Date یکتا برای یک قرارداد پرتکرار (نمونه‌ی کامل توالی) ---';
SELECT TOP 1 loanfile_id INTO #sample_loan FROM Loan_Remain GROUP BY loanfile_id ORDER BY COUNT(*) DESC;
SELECT DISTINCT Transaction_Date FROM Loan_Remain WHERE loanfile_id IN (SELECT loanfile_id FROM #sample_loan) ORDER BY Transaction_Date;
DROP TABLE #sample_loan;

PRINT '=== ۳. آیا میانگین ~۱۰۰ رکورد/قرارداد با فرکانس روزانه در ۶ سال (~۲۱۹۰ روز) سازگار است یا با فرکانس دیگری؟ ===';
SELECT COUNT(*) * 1.0 / COUNT(DISTINCT loanfile_id) AS avg_rows_per_loan FROM Loan_Remain;

PRINT '=== ۴. Deposit_Monthly_Activity: آیا برای هر (deposit_id, year_mount) دقیقاً یک رکورد هست؟ ===';
SELECT dup_count, COUNT(*) AS how_many_groups_have_this_many_rows
FROM (
    SELECT deposit_id, year_mount, COUNT(*) AS dup_count
    FROM Deposit_Monthly_Activity
    GROUP BY deposit_id, year_mount
) x
GROUP BY dup_count
ORDER BY dup_count;

PRINT '=== ۵. Customer_Monthly_Activity: آیا برای هر (main_customer_id, year_mount) دقیقاً یک رکورد هست؟ (بدون احتساب ردیف‌های کارمزد) ===';
SELECT dup_count, COUNT(*) AS how_many_groups
FROM (
    SELECT main_customer_id, year_mount, COUNT(*) AS dup_count
    FROM Customer_Monthly_Activity
    GROUP BY main_customer_id, year_mount
) x
GROUP BY dup_count
ORDER BY dup_count;

PRINT '--- نمونه یک مشتری با چند ردیف در یک ماه، برای دیدن اینکه آیا sum_creditor... در همه‌ی ردیف‌ها تکرار شده یا نه ---';
SELECT TOP 1 main_customer_id, year_mount, COUNT(*) c
INTO #sample_cust
FROM Customer_Monthly_Activity GROUP BY main_customer_id, year_mount HAVING COUNT(*) > 1 ORDER BY COUNT(*) DESC;
SELECT cma.* FROM Customer_Monthly_Activity cma
JOIN #sample_cust s ON s.main_customer_id = cma.main_customer_id AND s.year_mount = cma.year_mount;
DROP TABLE #sample_cust;

PRINT '=== ۶. Loan_Monthly_Activity: چند رکورد به‌ازای هر (loanfile_id, ماه پرداخت)؟ (طبیعتاً باید >1 باشد چون سطح قسط است) ===';
SELECT dup_count, COUNT(*) AS how_many_groups
FROM (
    SELECT loanfile_id, LEFT(LTRIM(RTRIM(REPLACE(payed_date, CHAR(34), ''))), 7) AS ym, COUNT(*) AS dup_count
    FROM Loan_Monthly_Activity
    WHERE payed_date IS NOT NULL AND LEN(LTRIM(RTRIM(payed_date))) >= 7
    GROUP BY loanfile_id, LEFT(LTRIM(RTRIM(REPLACE(payed_date, CHAR(34), ''))), 7)
) x
GROUP BY dup_count
ORDER BY dup_count;
