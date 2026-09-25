-- آمار پایه‌ی ۱۴ جدول برای docs/08_data_landscape_report.md: تعداد رکورد واقعی، تعداد موجودیت یکتا، بازه‌ی زمانی
SET NOCOUNT ON;
USE Alzahra_Final_DB;

PRINT '=== Customer_Profile ===';
SELECT COUNT(*) AS row_count, COUNT(DISTINCT Customer_id) AS distinct_customers FROM Customer_Profile;

PRINT '=== Deposit_Customer ===';
SELECT COUNT(*) AS row_count, COUNT(DISTINCT CUSTOMER_ID) AS distinct_customers FROM Deposit_Customer;

PRINT '=== Deposit_Accoutnt_Info ===';
SELECT COUNT(*) AS row_count, COUNT(DISTINCT DEPOSIT_ID) AS distinct_accounts,
       COUNT(DISTINCT LTRIM(RTRIM(MAIN_CUSTOMER_ID))) AS distinct_customers
FROM Deposit_Accoutnt_Info;
SELECT MIN(OPEN_DATE) AS min_open_date_str, MAX(OPEN_DATE) AS max_open_date_str FROM Deposit_Accoutnt_Info WHERE ISNUMERIC(LEFT(LTRIM(RTRIM(OPEN_DATE)),4))=1;

PRINT '=== Deposit_Monthly_Activity ===';
SELECT COUNT(*) AS row_count, COUNT(DISTINCT deposit_id) AS distinct_accounts,
       COUNT(DISTINCT customer_id) AS distinct_customers, MIN(year_mount) AS min_ym, MAX(year_mount) AS max_ym
FROM Deposit_Monthly_Activity;

PRINT '=== Loan_Grant_Customer ===';
SELECT COUNT(*) AS row_count, COUNT(DISTINCT ID) AS distinct_customers FROM Loan_Grant_Customer;

PRINT '=== Loan_Contract_Info ===';
SELECT COUNT(*) AS row_count, COUNT(DISTINCT LOANFILE_ID) AS distinct_loans,
       COUNT(DISTINCT MAIN_CUSTOMER_ID) AS distinct_customers FROM Loan_Contract_Info;
SELECT MIN(GRANT_DATE) AS min_grant_date, MAX(GRANT_DATE) AS max_grant_date FROM Loan_Contract_Info WHERE ISNUMERIC(LEFT(LTRIM(RTRIM(GRANT_DATE)),4))=1;

PRINT '=== Loan_Monthly_Activity ===';
SELECT COUNT(*) AS row_count, COUNT(DISTINCT loanfile_id) AS distinct_loans,
       MIN(LEFT(LTRIM(RTRIM(REPLACE(payed_date,CHAR(34),''))),7)) AS min_paydate,
       MAX(LEFT(LTRIM(RTRIM(REPLACE(payed_date,CHAR(34),''))),7)) AS max_paydate
FROM Loan_Monthly_Activity;

PRINT '=== Loan_Remain ===';
SELECT COUNT(*) AS row_count, COUNT(DISTINCT loanfile_id) AS distinct_loans,
       COUNT(DISTINCT customer_id) AS distinct_customers,
       MIN(Transaction_Date) AS min_td, MAX(Transaction_Date) AS max_td
FROM Loan_Remain;

PRINT '=== Loan_Remain_Customer ===';
SELECT COUNT(*) AS row_count, COUNT(DISTINCT ID) AS distinct_customers FROM Loan_Remain_Customer;

PRINT '=== Customer_Monthly_Activity ===';
SELECT COUNT(*) AS row_count, COUNT(DISTINCT main_customer_id) AS distinct_customers,
       MIN(year_mount) AS min_ym, MAX(year_mount) AS max_ym
FROM Customer_Monthly_Activity;

PRINT '=== Base_Branch ===';
SELECT COUNT(*) AS row_count, COUNT(DISTINCT BranchCode) AS distinct_branch_codes FROM Base_Branch;

PRINT '=== DepositIDInterest ===';
SELECT COUNT(*) AS row_count, COUNT(DISTINCT Depositid) AS distinct_accounts,
       MIN(REPLACE(REPLACE(Year_Mounth,CHAR(13),''),CHAR(10),'')) AS min_ym,
       MAX(REPLACE(REPLACE(Year_Mounth,CHAR(13),''),CHAR(10),'')) AS max_ym
FROM DepositIDInterest;

PRINT '=== Interset_branch_sum ===';
SELECT COUNT(*) AS row_count, COUNT(DISTINCT BranchCode) AS distinct_branches,
       MIN(REPLACE(REPLACE(Year_Mounth,CHAR(13),''),CHAR(10),'')) AS min_ym,
       MAX(REPLACE(REPLACE(Year_Mounth,CHAR(13),''),CHAR(10),'')) AS max_ym
FROM Interset_branch_sum;

PRINT '=== LoanFileID_Brnach ===';
SELECT COUNT(*) AS row_count, COUNT(DISTINCT ID) AS distinct_loans FROM LoanFileID_Brnach;

PRINT '=== TOP 5 SAMPLES ===';
SELECT TOP 5 * FROM Customer_Profile;
SELECT TOP 5 * FROM Deposit_Accoutnt_Info;
SELECT TOP 5 * FROM Deposit_Monthly_Activity ORDER BY year_mount DESC;
SELECT TOP 5 * FROM Loan_Contract_Info;
SELECT TOP 5 * FROM Loan_Monthly_Activity;
SELECT TOP 5 * FROM Loan_Remain ORDER BY Transaction_Date DESC;
SELECT TOP 5 * FROM Customer_Monthly_Activity ORDER BY year_mount DESC;
SELECT TOP 5 * FROM Base_Branch;
