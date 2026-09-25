-- پرچم «تسهیلات‌گیرنده فعال» — طبق docs/07_sampling_methodology.md بخش ۲:
-- برخلاف سپرده‌گذاران (فیلتر ۴معیاره RFM)، برای تسهیلات‌گیرندگان صرفاً «داشتن مانده تسهیلات جاری در سال ۱۴۰۴»
-- ملاک فعال بودن است (اقساط ماهانه یعنی رابطه‌ی مالی فعال؛ داده‌ی Recency/Frequency جداگانه برای تسهیلات موجود نیست).
-- گرین (Grain): یک ردیف به‌ازای هر customer_id تسهیلات‌گیرنده
--
-- ⚠️ DRAFT — اجرا/اعتبارسنجی نشده. باید در نشستی با دسترسی مستقیم SQL Server اجرا و با جدول ۳ گزارش
--    نمونه‌گیری (۱,۵۵۵,۸۳۳ حقیقی / ۲۷,۳۳۵ حقوقی) و با SUM مستقیم روی Loan_Remain مقایسه شود
--    (همان الگوی Sanity Check که در docs/06_phase1_sql_views.md برای ۹ View دیگر توضیح داده شده).
--
-- فرضیات این نسخه:
--   - Transaction_Date عددی به فرمت YYYYMMDD شمسی است (مثال ۱۴۰۴۱۲۲۹)؛ سال با تقسیم صحیح بر ۱۰۰۰۰ استخراج می‌شود.
--   - "مانده‌ی جاری" یعنی حداقل یکی از رکوردهای Loan_Remain آن customer_id در سال ۱۴۰۴، Total_Remain > 0 دارد.
--   - این View مستقیماً روی Loan_Remain کار می‌کند، نه روی vw_Loan_Remain_By_Branch_Month، چون آن View فقط
--     ۸۹.۴٪ پوشش شعبه دارد (بند ۵ در docs/06_phase1_sql_views.md) و نباید جمعیت مشتریان را کوچک‌تر از واقع نشان دهد.
--
-- ✅ رفع‌شده (نشست Claude Code بومی، 2026-08-30): `Transaction_Date / 10000` روی numeric نتیجه‌ی اعشاری
-- می‌دهد نه صحیح (همان باگی که در vw_Loan_Remain_By_Branch_Month پیدا و رفع شد) — با CAST به bigint اصلاح شد.
-- تأیید شد: Loan_Remain.Transaction_Date دقیقاً ماهانه است (یک رکورد در پایان هر ماه شمسی)، نه روزانه/نامنظم.

CREATE OR ALTER VIEW dbo.vw_Active_Loan_Customer_Flags AS
SELECT
    customer_id,
    MAX(CASE WHEN Total_Remain > 0 THEN 1 ELSE 0 END) AS is_active_loan_customer,
    MAX(Total_Remain)                                  AS max_total_remain_1404,
    COUNT(DISTINCT loanfile_id)                        AS distinct_loan_files_1404
FROM dbo.Loan_Remain
WHERE (CAST(Transaction_Date AS bigint) / 10000) = 1404
GROUP BY customer_id;
