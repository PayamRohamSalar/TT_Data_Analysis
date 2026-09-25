-- گردش و مانده‌ی سپرده‌ها به تفکیک نوع سپرده و ماه — منبع فاز ۱ (بخش «سپرده‌گذاران»)
-- هشدار پوشش: ~۳۷٪ ردیف‌های Deposit_Monthly_Activity به deposit_id ای اشاره دارند که در
-- Deposit_Accoutnt_Info یافت نشد (شرح در docs/05) -> این ردیف‌ها با نوع "نامشخص" جمع می‌شوند.
--
-- ✅ Materialized (2026-09-03): این View قبلاً مستقیماً روی ۱۱۳.۴ میلیون ردیف Join+COUNT(DISTINCT)
-- می‌زد که هم به‌خاطر یک باگ Join (رفع‌شده) و هم به‌خاطر عدم Push-down فیلتر از پشت دو COUNT(DISTINCT)
-- هم‌زمان (رفع‌شده با تجمیع دومرحله‌ای)، در عمل هم اجرای مستقیم و هم SELECT INTO یک‌باره روی کل
-- جدول (۴۰+ دقیقه، ۲۳ گیگ Spill روی tempdb) عملاً غیرقابل‌استفاده بود. راه‌حل نهایی: محاسبه‌ی سنگین
-- یک‌بار و به‌صورت قطعه‌قطعه (۷۲ ماه جدا، هرکدام ۱۵-۲۰ ثانیه، بدون Spill) در جدول واقعی
-- dbo.Fact_Deposit_Portfolio_Monthly ذخیره شد (اسکریپت: sql/adhoc/materialize_deposit_portfolio_chunked.sql).
-- این View فقط یک Passthrough آنیِ روی آن جدول کوچک (۵۰۴ ردیف) است.
-- ⚠️ چون داده‌ی منبع (بک‌آپ بانک) ثابت/منجمد است، نیازی به Refresh مجدد نیست؛ اگر روزی جدول خام
-- تغییر کرد، اسکریپت Chunked باید دوباره اجرا شود.
CREATE OR ALTER VIEW dbo.vw_Deposit_Portfolio_Monthly AS
SELECT year_mount, deposit_type, account_count, customer_count,
       total_credit_turnover, total_debit_turnover, credit_txn_count, debit_txn_count, avg_balance
FROM dbo.Fact_Deposit_Portfolio_Monthly;
