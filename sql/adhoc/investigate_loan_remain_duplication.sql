-- بررسی فوری و حیاتی: آیا Loan_Remain روی (loanfile_id, Transaction_Date) تکرار واقعی دارد؟
-- این تصحیح یک نتیجه‌گیری اشتباه در نشست قبلی است (docs/08_data_landscape_report.md، بخش ۲) —
-- آنجا "distinct_dates_in_month=1" به اشتباه به‌عنوان "۱ ردیف در ماه" تفسیر شد، در حالی‌که
-- rows_in_month همان زمان ۱۰ تا ۱۴ بود (یعنی تکرار، نه تک‌ردیفی).
SET NOCOUNT ON;
USE Alzahra_Final_DB;

PRINT '=== تعداد کل گروه‌های یکتای (loanfile_id, Transaction_Date) ===';
SELECT COUNT(*) AS total_distinct_groups FROM (
    SELECT loanfile_id, Transaction_Date FROM Loan_Remain GROUP BY loanfile_id, Transaction_Date
) x;

PRINT '=== آیا ردیف‌های تکراری دقیقاً یکسانند (همه‌ی ستون‌ها) یا مقادیر متفاوت دارند؟ ===';
SELECT TOP 1 loanfile_id, Transaction_Date INTO #dup_sample
FROM Loan_Remain GROUP BY loanfile_id, Transaction_Date HAVING COUNT(*) > 1
ORDER BY COUNT(*) DESC;
SELECT lr.* FROM Loan_Remain lr JOIN #dup_sample d ON d.loanfile_id=lr.loanfile_id AND d.Transaction_Date=lr.Transaction_Date;
DROP TABLE #dup_sample;

PRINT '=== نسبت ردیف خام به ردیف یکتا (ضریب تورم کلی) ===';
SELECT
    (SELECT COUNT(*) FROM Loan_Remain) AS raw_rows,
    (SELECT COUNT(*) FROM (SELECT DISTINCT loanfile_id, customer_id, ECO_SEC, MANDE_JARI, Overusance_Remain, Postponed_Remain, Doubtful_Remain, Total_Remain, Transaction_Date FROM Loan_Remain) x) AS fully_distinct_rows;

PRINT '=== اگر با SELECT DISTINCT کامل حذف تکرار کنیم، SUM(Total_Remain) برای آخرین ماه چقدر تغییر می‌کند؟ ===';
SELECT SUM(Total_Remain) AS sum_raw FROM Loan_Remain WHERE Transaction_Date = 14041229;
SELECT SUM(Total_Remain) AS sum_dedup FROM (
    SELECT DISTINCT loanfile_id, customer_id, ECO_SEC, MANDE_JARI, Overusance_Remain, Postponed_Remain, Doubtful_Remain, Total_Remain, Transaction_Date
    FROM Loan_Remain WHERE Transaction_Date = 14041229
) x;
