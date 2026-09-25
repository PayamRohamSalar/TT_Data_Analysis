-- آمار کامل ستون‌به‌ستون برای Table_Profiles.xlsx (۱۴ جدول)
SET NOCOUNT ON;
USE Alzahra_Final_DB;

PRINT '##### Customer_Profile #####';
SELECT SUM(CASE WHEN creator_branch IS NULL THEN 1 ELSE 0 END) null_branch,
       SUM(CASE WHEN age IS NULL THEN 1 ELSE 0 END) null_age,
       SUM(CASE WHEN sex_name IS NULL THEN 1 ELSE 0 END) null_sex,
       SUM(CASE WHEN job_name IS NULL OR LTRIM(RTRIM(REPLACE(job_name,CHAR(34),'')))='' THEN 1 ELSE 0 END) blank_job,
       SUM(CASE WHEN membership_info IS NULL OR LTRIM(RTRIM(REPLACE(membership_info,CHAR(34),'')))='' THEN 1 ELSE 0 END) blank_mi,
       MIN(age) min_age, MAX(age) max_age, AVG(CAST(age AS float)) avg_age
FROM Customer_Profile;
SELECT TOP 10 LTRIM(RTRIM(REPLACE(job_name,CHAR(34),''))) v, COUNT(*) c FROM Customer_Profile GROUP BY LTRIM(RTRIM(REPLACE(job_name,CHAR(34),''))) ORDER BY c DESC;
SELECT COUNT(DISTINCT LTRIM(RTRIM(REPLACE(job_name,CHAR(34),'')))) distinct_job FROM Customer_Profile;
SELECT COUNT(*) dup_rows FROM (SELECT Customer_id FROM Customer_Profile GROUP BY Customer_id HAVING COUNT(*)>1) x;

PRINT '##### Deposit_Customer #####';
SELECT COUNT(*) dup_rows FROM (SELECT CUSTOMER_ID FROM Deposit_Customer GROUP BY CUSTOMER_ID HAVING COUNT(*)>1) x;

PRINT '##### Deposit_Accoutnt_Info #####';
SELECT
  SUM(CASE WHEN CLOSE_DATE IS NULL OR LTRIM(RTRIM(CLOSE_DATE))='' THEN 1 ELSE 0 END) null_close,
  SUM(CASE WHEN EXPIRE_DATE IS NULL OR LTRIM(RTRIM(EXPIRE_DATE))='' THEN 1 ELSE 0 END) null_expire
FROM Deposit_Accoutnt_Info;
SELECT LTRIM(RTRIM(REPLACE(STATUS_NAME,CHAR(34),''))) v, COUNT(*) c FROM Deposit_Accoutnt_Info GROUP BY LTRIM(RTRIM(REPLACE(STATUS_NAME,CHAR(34),''))) ORDER BY c DESC;
SELECT LTRIM(RTRIM(REPLACE(MAINTYPE_NAME,CHAR(34),''))) v, COUNT(*) c FROM Deposit_Accoutnt_Info GROUP BY LTRIM(RTRIM(REPLACE(MAINTYPE_NAME,CHAR(34),''))) ORDER BY c DESC;
SELECT COUNT(*) dup_rows FROM (SELECT DEPOSIT_ID FROM Deposit_Accoutnt_Info GROUP BY DEPOSIT_ID HAVING COUNT(*)>1) x;

PRINT '##### Deposit_Monthly_Activity #####';
SELECT MIN(sum_creditor_circul_amount_eq) mn_cr, MAX(sum_creditor_circul_amount_eq) mx_cr, AVG(sum_creditor_circul_amount_eq) avg_cr,
       MIN(sum_debtor_circul_amount_eq) mn_db, MAX(sum_debtor_circul_amount_eq) mx_db, AVG(sum_debtor_circul_amount_eq) avg_db,
       MIN(avr_total_amount_eq) mn_avr, MAX(avr_total_amount_eq) mx_avr, AVG(avr_total_amount_eq) avg_avr
FROM Deposit_Monthly_Activity;

PRINT '##### Loan_Grant_Customer #####';
SELECT COUNT(*) dup_rows FROM (SELECT ID FROM Loan_Grant_Customer GROUP BY ID HAVING COUNT(*)>1) x;

PRINT '##### Loan_Contract_Info #####';
SELECT COUNT(DISTINCT LTRIM(RTRIM(REPLACE(LOAN_TYPE_DESCRIPTION,CHAR(34),'')))) distinct_loan_type FROM Loan_Contract_Info;
SELECT TOP 10 LTRIM(RTRIM(REPLACE(LOAN_TYPE_DESCRIPTION,CHAR(34),''))) v, COUNT(*) c FROM Loan_Contract_Info GROUP BY LTRIM(RTRIM(REPLACE(LOAN_TYPE_DESCRIPTION,CHAR(34),''))) ORDER BY c DESC;
SELECT MIN(GRANT_AMOUNT) mn_g, MAX(GRANT_AMOUNT) mx_g, AVG(CAST(GRANT_AMOUNT AS float)) avg_g,
       MIN(APPROVED_AMOUNT) mn_a, MAX(APPROVED_AMOUNT) mx_a, AVG(CAST(APPROVED_AMOUNT AS float)) avg_a,
       MIN(USED_COST) mn_u, MAX(USED_COST) mx_u, AVG(CAST(USED_COST AS float)) avg_u,
       MIN(DURATION_DAYS) mn_d, MAX(DURATION_DAYS) mx_d, AVG(CAST(DURATION_DAYS AS float)) avg_d
FROM Loan_Contract_Info;
SELECT COUNT(*) dup_rows FROM (SELECT LOANFILE_ID FROM Loan_Contract_Info GROUP BY LOANFILE_ID HAVING COUNT(*)>1) x;

PRINT '##### Loan_Monthly_Activity #####';
SELECT MIN(installment_main) mn_m, MAX(installment_main) mx_m, AVG(installment_main) avg_m,
       MIN(installment_interest) mn_i, MAX(installment_interest) mx_i, AVG(installment_interest) avg_i,
       MIN(installment_penalty) mn_p, MAX(installment_penalty) mx_p, AVG(installment_penalty) avg_p,
       SUM(CASE WHEN payed_date IS NULL THEN 1 ELSE 0 END) null_payed,
       SUM(CASE WHEN delivery_date IS NULL THEN 1 ELSE 0 END) null_delivery
FROM Loan_Monthly_Activity;

PRINT '##### Loan_Remain #####';
SELECT MIN(MANDE_JARI) mn1, MAX(MANDE_JARI) mx1, AVG(MANDE_JARI) avg1,
       MIN(Total_Remain) mn2, MAX(Total_Remain) mx2, AVG(Total_Remain) avg2,
       MIN(Overusance_Remain) mn3, MAX(Overusance_Remain) mx3,
       MIN(Postponed_Remain) mn4, MAX(Postponed_Remain) mx4,
       MIN(Doubtful_Remain) mn5, MAX(Doubtful_Remain) mx5
FROM Loan_Remain;
SELECT COUNT(*) dup_on_natural_key FROM (SELECT loanfile_id, Transaction_Date FROM Loan_Remain GROUP BY loanfile_id, Transaction_Date HAVING COUNT(*)>1) x;

PRINT '##### Loan_Remain_Customer #####';
SELECT COUNT(*) dup_rows FROM (SELECT ID FROM Loan_Remain_Customer GROUP BY ID HAVING COUNT(*)>1) x;

PRINT '##### Customer_Monthly_Activity #####';
SELECT MIN(amount_eq) mn_ae, MAX(amount_eq) mx_ae, AVG(amount_eq) avg_ae FROM Customer_Monthly_Activity;
SELECT COUNT(*) dup_exact FROM (
    SELECT main_customer_id, year_mount, code, title, amount_eq FROM Customer_Monthly_Activity
    GROUP BY main_customer_id, year_mount, code, title, amount_eq HAVING COUNT(*)>1
) x;

PRINT '##### Base_Branch #####';
SELECT COUNT(*) total, COUNT(DISTINCT ID) distinct_id, COUNT(DISTINCT BranchCode) distinct_code,
       SUM(CASE WHEN BranchName IS NULL THEN 1 ELSE 0 END) null_name
FROM Base_Branch;

PRINT '##### DepositIDInterest #####';
SELECT MIN(Amount) mn, MAX(Amount) mx, AVG(Amount) avg FROM DepositIDInterest;

PRINT '##### Interset_branch_sum #####';
SELECT MIN(Amount) mn, MAX(Amount) mx, AVG(Amount) avg FROM Interset_branch_sum;
SELECT COUNT(*) dup_on_key FROM (
    SELECT REPLACE(REPLACE(BranchCode,CHAR(13),''),CHAR(10),'') bc, REPLACE(REPLACE(Year_Mounth,CHAR(13),''),CHAR(10),'') ym
    FROM Interset_branch_sum
    GROUP BY REPLACE(REPLACE(BranchCode,CHAR(13),''),CHAR(10),''), REPLACE(REPLACE(Year_Mounth,CHAR(13),''),CHAR(10),'')
    HAVING COUNT(*)>1
) x;

PRINT '##### LoanFileID_Brnach #####';
SELECT COUNT(*) dup_rows FROM (SELECT ID FROM LoanFileID_Brnach GROUP BY ID HAVING COUNT(*)>1) x;
SELECT TOP 5 ID, COUNT(DISTINCT REPLACE(BranchCode,CHAR(13),'')) distinct_branches_for_this_loan
FROM LoanFileID_Brnach GROUP BY ID HAVING COUNT(*)>1 ORDER BY COUNT(*) DESC;
