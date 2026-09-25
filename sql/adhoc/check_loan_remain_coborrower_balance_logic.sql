SET NOCOUNT ON;
USE Alzahra_Final_DB;

PRINT '=== نمونه‌ی وام چند-مشتری با مانده‌ی غیرصفر در یک ماه ===';
SELECT TOP 1 loanfile_id, Transaction_Date
INTO #multi
FROM Loan_Remain
WHERE Total_Remain > 0
GROUP BY loanfile_id, Transaction_Date
HAVING COUNT(DISTINCT customer_id) > 1
ORDER BY COUNT(DISTINCT customer_id) DESC;

SELECT lr.* FROM Loan_Remain lr JOIN #multi m ON m.loanfile_id=lr.loanfile_id AND m.Transaction_Date=lr.Transaction_Date;
DROP TABLE #multi;

PRINT '=== آمار کلی: چند درصد گروه‌های (loanfile_id, Transaction_Date) با مانده غیرصفر، بیش از ۱ customer_id دارند؟ ===';
SELECT
    SUM(CASE WHEN cnt_cust > 1 THEN 1 ELSE 0 END) AS multi_customer_groups,
    COUNT(*) AS total_groups_nonzero
FROM (
    SELECT loanfile_id, Transaction_Date, COUNT(DISTINCT customer_id) AS cnt_cust
    FROM Loan_Remain
    WHERE Total_Remain > 0
    GROUP BY loanfile_id, Transaction_Date
) x;

PRINT '=== مقایسه‌ی SUM(Total_Remain) خام در برابر SUM بعد از انتخاب فقط ۱ ردیف به‌ازای هر (loanfile_id, ماه) — آخرین ماه ===';
SELECT SUM(Total_Remain) AS sum_raw_all_customers FROM Loan_Remain WHERE Transaction_Date = 14041229;

;WITH OnePerLoan AS (
    SELECT loanfile_id, Total_Remain,
           ROW_NUMBER() OVER (PARTITION BY loanfile_id ORDER BY customer_id) AS rn
    FROM Loan_Remain WHERE Transaction_Date = 14041229
)
SELECT SUM(Total_Remain) AS sum_one_row_per_loan FROM OnePerLoan WHERE rn = 1;
