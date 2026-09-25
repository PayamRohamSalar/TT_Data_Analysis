SET NOCOUNT ON;
USE Alzahra_Final_DB;

PRINT '=== سپرده‌گذاران فعال (نسخه‌ی اصلاح‌شده) ===';
SELECT COUNT(*) AS total_depositors, SUM(is_active_depositor) AS active_depositors,
       CAST(SUM(is_active_depositor) AS FLOAT) / COUNT(*) AS active_share
FROM vw_Active_Depositor_Flags;

PRINT '=== آیا جمعیت تسهیلات‌گیرنده (از Loan_Remain) کامل است؟ مقایسه با Loan_Contract_Info/Loan_Grant_Customer ===';
SELECT COUNT(DISTINCT MAIN_CUSTOMER_ID) AS total_in_contract_info FROM Loan_Contract_Info;
SELECT COUNT(DISTINCT ID) AS total_in_grant_customer FROM Loan_Grant_Customer;
SELECT COUNT(*) AS union_population FROM (
    SELECT customer_id AS cid FROM Loan_Remain
    UNION
    SELECT MAIN_CUSTOMER_ID FROM Loan_Contract_Info
    UNION
    SELECT ID FROM Loan_Grant_Customer
) u;

PRINT '=== تسهیلات‌گیرندگان فعال (بعد از رفع باگ division) ===';
SELECT COUNT(*) AS total_loan_customers, SUM(is_active_loan_customer) AS active_loan_customers,
       CAST(SUM(is_active_loan_customer) AS FLOAT) / COUNT(*) AS active_share
FROM vw_Active_Loan_Customer_Flags;
