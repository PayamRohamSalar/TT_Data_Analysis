-- رفع مشکل کارایی حیاتی (نشست ۲۰۲۶-۰۹-۰۴): بازسازی IX_LoanRemain_LoanDate_Customer با INCLUDE
-- ریشه‌ی مشکل: Loan_Remain یک Heap خالص است (بدون Clustered Index). ایندکس موجود
-- (loanfile_id, Transaction_Date, customer_id) دقیقاً با partition/order کوئری‌های
-- ROW_NUMBER() OVER (PARTITION BY loanfile_id, Transaction_Date ORDER BY customer_id) که در
-- vw_Loan_Remain_By_Branch_Month و همه‌ی اسکریپت‌های فاز ۱ استفاده می‌شود، هم‌خوان است — ولی چون
-- ستون‌های مبلغی (ECO_SEC, MANDE_JARI, Total_Remain, ...) در آن INCLUDE نشده‌اند، SQL Server برای هر
-- ردیف یک RID Lookup جداگانه به Heap می‌زند. روی ده‌ها میلیون ردیف این عملاً غیرقابل‌تحمل است (کوئری
-- بدون فیلتر روی کل جدول حتی با ۴۰۰ ثانیه هم Timeout داد؛ نسخه‌ی تک‌ماهه هم ~۱۹ ثانیه طول کشید).
-- این دقیقاً همان الگوی ۷ ایندکس پوششی است که در ۲۰۲۶-۰۸-۳۰ برای ۵ جدول دیگر ساخته شد
-- (sql/adhoc/create_core_table_indexes.sql, _part2.sql).
CREATE NONCLUSTERED INDEX IX_LoanRemain_LoanDate_Customer
ON dbo.Loan_Remain (loanfile_id, Transaction_Date, customer_id)
INCLUDE (ECO_SEC, MANDE_JARI, Overusance_Remain, Postponed_Remain, Doubtful_Remain, Total_Remain)
WITH (DROP_EXISTING = ON);
