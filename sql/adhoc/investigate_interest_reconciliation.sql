-- بررسی علت اختلاف بین DepositIDInterest (سطح حساب) و Interset_branch_sum (سطح شعبه)
-- نتیجه‌ی کامل و تفسیر در docs/06_phase1_sql_views.md (بند ۶). خلاصه: DepositIDInterest ردیف تکراری
-- عیناً یکسان دارد (تا ۶۳ بار برای یک حساب)، ولی چون شناسه‌ی تراکنش ندارد، حذف تکرار با DISTINCT هم
-- عدد را دقیقاً با جدول مرجع بانک یکی نمی‌کند. سه عدد را به‌عنوان بازه‌ی عدم‌قطعیت در نظر بگیرید.
SET NOCOUNT ON;
USE Alzahra_Final_DB;

DECLARE @ym_di varchar(10) = '140412';   -- فرمت DepositIDInterest: بدون جداکننده
DECLARE @ym_ibs varchar(10) = '1404/12'; -- فرمت Interset_branch_sum: با اسلش

PRINT '=== سه عدد برای یک ماه ===';
SELECT SUM(Amount) AS naive_sum
FROM DepositIDInterest
WHERE REPLACE(REPLACE(Year_Mounth,CHAR(13),''),CHAR(10),'') = @ym_di;

SELECT SUM(Amount) AS dedup_sum FROM (
    SELECT DISTINCT Depositid, BranchCode, Amount, Year_Mounth
    FROM DepositIDInterest
    WHERE REPLACE(REPLACE(Year_Mounth,CHAR(13),''),CHAR(10),'') = @ym_di
) x;

SELECT SUM(Amount) AS bank_branch_sum
FROM Interset_branch_sum
WHERE REPLACE(REPLACE(Year_Mounth,CHAR(13),''),CHAR(10),'') = @ym_ibs;

PRINT '=== نمونه‌ی تکرار محض (۶۳ ردیف عیناً یکسان) ===';
SELECT Depositid, COUNT(*) row_cnt, COUNT(DISTINCT Amount) distinct_amounts
FROM DepositIDInterest
WHERE REPLACE(REPLACE(Year_Mounth,CHAR(13),''),CHAR(10),'') = @ym_di
GROUP BY Depositid HAVING COUNT(*) > 1
ORDER BY COUNT(*) DESC;
