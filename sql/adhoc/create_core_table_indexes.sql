-- ایندکس‌های پوششی روی جداول بزرگ که قبلاً کاملاً Heap بودند (بدون هیچ ایندکسی) — علت اصلی
-- کندی مزمن کوئری‌های این پروژه. هر ایندکس دقیقاً برای الگوی Join/GROUP BY رایج این جدول در
-- View های فاز ۱ طراحی شده. اجرا: 2026-08-30.
USE Alzahra_Final_DB;

-- Deposit_Monthly_Activity (۱۱۳.۴ میلیون ردیف) — Join با deposit_id، GROUP BY با customer_id/year_mount
CREATE NONCLUSTERED INDEX IX_DepositMonthlyActivity_DepositId
ON dbo.Deposit_Monthly_Activity (deposit_id, year_mount)
INCLUDE (sum_creditor_circul_amount_eq, sum_debtor_circul_amount_eq, sum_creditor_circul_count, sum_debtor_circul_count, avr_total_amount_eq, customer_id);

CREATE NONCLUSTERED INDEX IX_DepositMonthlyActivity_CustomerId
ON dbo.Deposit_Monthly_Activity (customer_id, year_mount)
INCLUDE (avr_total_amount_eq, sum_creditor_circul_count, sum_debtor_circul_count);

-- Deposit_Accoutnt_Info (۱.۵ میلیون ردیف) — Join با DEPOSIT_ID برای dedup و اتصال به Monthly_Activity
CREATE NONCLUSTERED INDEX IX_DepositAccountInfo_DepositId
ON dbo.Deposit_Accoutnt_Info (DEPOSIT_ID)
INCLUDE (MAIN_CUSTOMER_ID, MAINTYPE_NAME, STATUS_NAME, OPEN_DATE, CLOSE_DATE);

-- Customer_Monthly_Activity (۳۳.۲ میلیون ردیف) — پایه‌ی vw_Customer_Turnover_Monthly (DISTINCT سنگین)
CREATE NONCLUSTERED INDEX IX_CustomerMonthlyActivity_CustomerId
ON dbo.Customer_Monthly_Activity (main_customer_id, year_mount)
INCLUDE (sum_creditor_circul_amount_eq, sum_debtor_circul_amount_eq, sum_creditor_circul_count, sum_debtor_circul_count);

-- Loan_Monthly_Activity (۱۷ میلیون ردیف) — Join با loanfile_id
CREATE NONCLUSTERED INDEX IX_LoanMonthlyActivity_LoanfileId
ON dbo.Loan_Monthly_Activity (loanfile_id)
INCLUDE (installment_main, installment_interest, installment_penalty, Status, payed_date, delivery_date);

-- Loan_Contract_Info (۷۸۰ هزار ردیف) — Join با LOANFILE_ID/MAIN_CUSTOMER_ID
CREATE NONCLUSTERED INDEX IX_LoanContractInfo_LoanfileId
ON dbo.Loan_Contract_Info (LOANFILE_ID)
INCLUDE (MAIN_CUSTOMER_ID, LOAN_TYPE_DESCRIPTION, GRANT_AMOUNT, APPROVED_AMOUNT, LOAN_INTEREST_RATE, LOAN_PREFERED_RATE, USED_COST);

CREATE NONCLUSTERED INDEX IX_LoanContractInfo_CustomerId
ON dbo.Loan_Contract_Info (MAIN_CUSTOMER_ID);

PRINT 'همه‌ی ایندکس‌ها ساخته شدند.';
