-- نگاشت یک‌به‌یک deposit_id -> نوع/وضعیت سپرده (Deposit_Accoutnt_Info تکرار دارد؛ تأیید شد نوع سپرده در تکرارها همیشه یکسان است)
--
-- ✅ رفع باگ کارایی حیاتی (2026-08-31): deposit_id قبلاً varchar خروجی می‌داد و در vw_Deposit_Portfolio_Monthly
-- با CAST(dma.deposit_id AS varchar(30)) مقایسه می‌شد — یعنی ستون عددی ایندکس‌شده‌ی جدول ۱۱۳ میلیون‌ردیفی
-- Deposit_Monthly_Activity داخل یک expression پیچیده می‌شد و ایندکس قابل‌استفاده نبود (Join روی ۱۱۳M ردیف
-- با Nested Loop به‌جای Hash/Merge، باعث اجرای ۹+ ساعته‌ی بدون نتیجه شد). با خروجی numeric، سمت کوچک
-- (۱.۵ میلیون ردیف dedup‌شده) cast می‌شود، نه سمت بزرگ — ایندکس IX_DepositMonthlyActivity_DepositId کامل استفاده می‌شود.
CREATE OR ALTER VIEW dbo.vw_Deposit_Account_Dedup AS
SELECT
    CAST(LTRIM(RTRIM(DEPOSIT_ID)) AS numeric(38,0))       AS deposit_id,
    MIN(LTRIM(RTRIM(MAIN_CUSTOMER_ID)))                   AS main_customer_id,
    MIN(LTRIM(RTRIM(MAINTYPE_NAME)))                      AS deposit_type,
    MIN(OPEN_DATE)                                        AS open_date,
    MAX(CLOSE_DATE)                                       AS close_date  -- اگر هر رکورد بسته شد، تاریخ بسته‌شدن لحاظ شود
FROM dbo.Deposit_Accoutnt_Info
GROUP BY LTRIM(RTRIM(DEPOSIT_ID));
