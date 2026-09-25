-- بررسی پوشش (Orphan Rate) هر رابطه‌ی کلیدی بین جداول Alzahra_Final_DB
-- نتایج کامل و تفسیر در docs/05_entity_relationships.md مستند شده؛ این فایل برای اجرای مجدد بعد از هر تغییر داده نگه داشته شده.
SET NOCOUNT ON;
USE Alzahra_Final_DB;

PRINT '=== Deposit_Monthly_Activity.deposit_id -> Deposit_Accoutnt_Info.DEPOSIT_ID ===';
SELECT COUNT(*) AS total_rows,
       SUM(CASE WHEN da.DEPOSIT_ID IS NULL THEN 1 ELSE 0 END) AS orphan_rows
FROM Deposit_Monthly_Activity dma
LEFT JOIN Deposit_Accoutnt_Info da ON CAST(dma.deposit_id AS varchar(30)) = LTRIM(RTRIM(da.DEPOSIT_ID));

PRINT '=== Loan_Remain.loanfile_id -> Loan_Contract_Info.LOANFILE_ID ===';
SELECT COUNT(*) AS total_rows,
       SUM(CASE WHEN lci.LOANFILE_ID IS NULL THEN 1 ELSE 0 END) AS orphan_rows
FROM Loan_Remain lr
LEFT JOIN Loan_Contract_Info lci ON lr.loanfile_id = lci.LOANFILE_ID;

PRINT '=== Loan_Remain.loanfile_id -> LoanFileID_Brnach.ID (branch coverage via bonus table) ===';
SELECT COUNT(*) AS total_rows,
       SUM(CASE WHEN lfb.ID IS NULL THEN 1 ELSE 0 END) AS orphan_rows
FROM Loan_Remain lr
LEFT JOIN (SELECT DISTINCT ID, BranchCode FROM LoanFileID_Brnach) lfb
    ON CAST(lr.loanfile_id AS varchar(30)) = lfb.ID;

PRINT '=== Customer_Profile.creator_branch -> Base_Branch.ID ===';
SELECT COUNT(DISTINCT cp.creator_branch) AS distinct_creator_branch,
       SUM(CASE WHEN bb.ID IS NULL THEN 1 ELSE 0 END) AS unmatched_customer_rows
FROM Customer_Profile cp
LEFT JOIN Base_Branch bb ON LTRIM(RTRIM(cp.creator_branch)) = LTRIM(RTRIM(bb.ID));
