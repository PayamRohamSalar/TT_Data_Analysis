-- بررسی حیاتی: آیا جمعیت پایه‌ی vw_Active_Depositor_Flags (از Customer_Monthly_Activity) کوچک‌تر از واقعیت است؟
SET NOCOUNT ON;
USE Alzahra_Final_DB;

PRINT '=== آیا همه‌ی مشتریان Deposit_Accoutnt_Info در Customer_Monthly_Activity هم هستند؟ ===';
SELECT COUNT(DISTINCT LTRIM(RTRIM(da.MAIN_CUSTOMER_ID))) AS total_deposit_customers,
       COUNT(DISTINCT CASE WHEN cma.main_customer_id IS NOT NULL THEN LTRIM(RTRIM(da.MAIN_CUSTOMER_ID)) END) AS also_in_cma
FROM Deposit_Accoutnt_Info da
LEFT JOIN (SELECT DISTINCT main_customer_id FROM Customer_Monthly_Activity) cma
    ON cma.main_customer_id = CAST(LTRIM(RTRIM(da.MAIN_CUSTOMER_ID)) AS numeric(38,0));

PRINT '=== جمعیت واقعی CustomerHub: اتحاد تمام منابع مشتری ===';
SELECT COUNT(*) AS union_population FROM (
    SELECT main_customer_id AS cid FROM Customer_Monthly_Activity
    UNION
    SELECT CAST(LTRIM(RTRIM(MAIN_CUSTOMER_ID)) AS numeric(38,0)) FROM Deposit_Accoutnt_Info
    UNION
    SELECT MAIN_CUSTOMER_ID FROM Loan_Contract_Info
    UNION
    SELECT customer_id FROM Loan_Remain
    UNION
    SELECT CUSTOMER_ID FROM Deposit_Customer
) u;
