-- نگاشت یک‌به‌یک تسهیلات -> شعبه (LoanFileID_Brnach خام تکرار دارد؛ تأیید شد هر loanfile_id همیشه به یک شعبه‌ی یکسان اشاره می‌کند - شرح در docs/05)
CREATE OR ALTER VIEW dbo.vw_Loan_Branch_Map AS
SELECT DISTINCT
    CAST(REPLACE(LTRIM(RTRIM(lfb.ID)), CHAR(13), '') AS bigint) AS loanfile_id,
    REPLACE(LTRIM(RTRIM(lfb.BranchCode)), CHAR(13), '')         AS branch_code
FROM dbo.LoanFileID_Brnach lfb;
