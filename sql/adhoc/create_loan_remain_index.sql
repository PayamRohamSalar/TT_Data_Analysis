-- ایندکس پوششی برای تسریع vw_Loan_Remain_By_Branch_Month (ROW_NUMBER روی loanfile_id+Transaction_Date)
-- جدول قبلاً HEAP بود با فقط یک ایندکس روی loanfile_id تنها؛ این باعث Sort سنگین روی ۷۰ میلیون ردیف می‌شد.
USE Alzahra_Final_DB;
CREATE NONCLUSTERED INDEX IX_LoanRemain_LoanDate_Customer
ON dbo.Loan_Remain (loanfile_id, Transaction_Date, customer_id)
INCLUDE (ECO_SEC, MANDE_JARI, Overusance_Remain, Postponed_Remain, Doubtful_Remain, Total_Remain);
