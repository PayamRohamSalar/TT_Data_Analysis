USE Alzahra_Final_DB;
SET QUOTED_IDENTIFIER ON;

-- DEPOSIT_ID در Deposit_Accoutnt_Info از نوع nvarchar(MAX) است — نمی‌تواند مستقیماً کلید ایندکس باشد.
-- یک ستون محاسبه‌شده‌ی persisted با طول ثابت اضافه می‌شود تا قابل ایندکس شود.
ALTER TABLE dbo.Deposit_Accoutnt_Info
ADD DEPOSIT_ID_KEY AS CONVERT(varchar(30), DEPOSIT_ID) PERSISTED;

CREATE NONCLUSTERED INDEX IX_DepositAccountInfo_DepositId
ON dbo.Deposit_Accoutnt_Info (DEPOSIT_ID_KEY)
INCLUDE (MAIN_CUSTOMER_ID, MAINTYPE_NAME, STATUS_NAME, OPEN_DATE, CLOSE_DATE);

-- Customer_Monthly_Activity (۳۳.۲ میلیون ردیف)
CREATE NONCLUSTERED INDEX IX_CustomerMonthlyActivity_CustomerId
ON dbo.Customer_Monthly_Activity (main_customer_id, year_mount)
INCLUDE (sum_creditor_circul_amount_eq, sum_debtor_circul_amount_eq, sum_creditor_circul_count, sum_debtor_circul_count);

-- Loan_Monthly_Activity (۱۷ میلیون ردیف)
CREATE NONCLUSTERED INDEX IX_LoanMonthlyActivity_LoanfileId
ON dbo.Loan_Monthly_Activity (loanfile_id)
INCLUDE (installment_main, installment_interest, installment_penalty, Status, payed_date, delivery_date);

-- Loan_Contract_Info (۷۸۰ هزار ردیف)
CREATE NONCLUSTERED INDEX IX_LoanContractInfo_LoanfileId
ON dbo.Loan_Contract_Info (LOANFILE_ID)
INCLUDE (MAIN_CUSTOMER_ID, LOAN_TYPE_DESCRIPTION, GRANT_AMOUNT, APPROVED_AMOUNT, LOAN_INTEREST_RATE, LOAN_PREFERED_RATE, USED_COST);

CREATE NONCLUSTERED INDEX IX_LoanContractInfo_CustomerId
ON dbo.Loan_Contract_Info (MAIN_CUSTOMER_ID);

PRINT 'بخش دوم ایندکس‌ها ساخته شد.';
