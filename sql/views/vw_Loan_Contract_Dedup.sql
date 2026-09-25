-- نگاشت یک‌به‌یک قرارداد تسهیلات (Loan_Contract_Info خام روی LOANFILE_ID تکرار دارد، ۷۸,۰۶۸ گروه —
-- شرح در reports/data_profile/Table_Profiles.xlsx، تب Loan_Contract_Info). یک ردیف قطعی به‌ازای هر
-- LOANFILE_ID با ROW_NUMBER انتخاب می‌شود (بدون فرض یکسان‌بودن محتوای تکرارها).
CREATE OR ALTER VIEW dbo.vw_Loan_Contract_Dedup AS
WITH Ranked AS (
    SELECT
        LOANFILE_ID, MAIN_CUSTOMER_ID, LOAN_TYPE_DESCRIPTION,
        GRANT_AMOUNT, APPROVED_AMOUNT, GRANT_DATE, DURATION_DAYS,
        LOAN_INTEREST_RATE, LOAN_PREFERED_RATE, USED_COST,
        ROW_NUMBER() OVER (PARTITION BY LOANFILE_ID ORDER BY MAIN_CUSTOMER_ID) AS rn
    FROM dbo.Loan_Contract_Info
)
SELECT
    LOANFILE_ID AS loanfile_id,
    MAIN_CUSTOMER_ID AS main_customer_id,
    LTRIM(RTRIM(REPLACE(LOAN_TYPE_DESCRIPTION, CHAR(34), ''))) AS loan_type_description,
    GRANT_AMOUNT AS grant_amount,
    APPROVED_AMOUNT AS approved_amount,
    GRANT_DATE AS grant_date,
    DURATION_DAYS AS duration_days,
    LOAN_INTEREST_RATE AS loan_interest_rate,
    LOAN_PREFERED_RATE AS loan_prefered_rate,
    USED_COST AS used_cost
FROM Ranked
WHERE rn = 1;
