-- بعد کمکی شعبه: نسخه‌ی پاک‌سازی‌شده‌ی Base_Branch (حذف کاراکترهای مخفی احتمالی، trim کامل)
-- استفاده: مرجع مشترک برای join با BranchCode در همه‌ی جداول تراکنشی (LoanFileID_Brnach, DepositIDInterest, Interset_branch_sum)
CREATE OR ALTER VIEW dbo.vw_Branch_Dim AS
SELECT
    LTRIM(RTRIM(REPLACE(REPLACE(ID, CHAR(13), ''), CHAR(10), '')))         AS creator_branch_id,  -- join با Customer_Profile.creator_branch (فعلاً بلااستفاده تا رفع مشکل CustomerHub)
    LTRIM(RTRIM(REPLACE(REPLACE(BranchCode, CHAR(13), ''), CHAR(10), ''))) AS branch_code,
    LTRIM(RTRIM(BranchName))                                              AS branch_name,
    LTRIM(RTRIM(ProvinceName))                                            AS city_name,           -- توجه: این ستون در عمل «شهر» است نه استان (شرح در docs/04)
    LTRIM(RTRIM(BranchTypeName))                                          AS branch_org_level,     -- شعبه / سرپرستی / ستاد
    CASE WHEN LTRIM(RTRIM(REPLACE(ID, CHAR(13), ''))) = '30789375629' THEN 1 ELSE 0 END AS is_virtual_branch
FROM dbo.Base_Branch;
