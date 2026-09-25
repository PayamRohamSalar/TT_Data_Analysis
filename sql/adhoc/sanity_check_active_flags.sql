-- Sanity Check: مقایسه‌ی vw_Active_Depositor_Flags / vw_Active_Loan_Customer_Flags با جدول ۳ گزارش نمونه‌گیری
SET NOCOUNT ON;
USE Alzahra_Final_DB;

PRINT '=== سپرده‌گذاران فعال (کل) ===';
SELECT COUNT(*) AS total_depositors, SUM(is_active_depositor) AS active_depositors,
       CAST(SUM(is_active_depositor) AS FLOAT) / COUNT(*) AS active_share
FROM vw_Active_Depositor_Flags;

PRINT '=== تسهیلات‌گیرندگان فعال (کل) ===';
SELECT COUNT(*) AS total_loan_customers, SUM(is_active_loan_customer) AS active_loan_customers,
       CAST(SUM(is_active_loan_customer) AS FLOAT) / COUNT(*) AS active_share
FROM vw_Active_Loan_Customer_Flags;

PRINT '=== breakdown جزئیات Recency/Frequency/Monetary/Tenure سپرده‌گذاران (چند نفر هر شرط را رد می‌کنند؟) ===';
SELECT
    SUM(CASE WHEN is_recent=0 THEN 1 ELSE 0 END) AS fail_recency,
    SUM(CASE WHEN active_months_count=0 THEN 1 ELSE 0 END) AS fail_frequency,
    SUM(CASE WHEN max_balance IS NULL OR max_balance < 5000000 THEN 1 ELSE 0 END) AS fail_monetary,
    SUM(CASE WHEN tenure_months IS NULL OR tenure_months < 12 THEN 1 ELSE 0 END) AS fail_tenure,
    COUNT(*) AS total
FROM vw_Active_Depositor_Flags;
