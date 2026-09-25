-- تبدیل vw_Deposit_Portfolio_Monthly به یک جدول واقعی (Materialized) — رفع قطعی مشکل کارایی.
-- علت: این View روی ۱۱۳.۴ میلیون ردیف Join+COUNT(DISTINCT)+GROUP BY می‌زد؛ چون داده‌ی این پروژه
-- ثابت است (بک‌آپ منجمد، نه سیستم زنده)، محاسبه‌ی سنگین فقط یک‌بار انجام و در یک جدول کوچک
-- (~۵۰۰ ردیف: ۷۲ ماه × ~۷ نوع سپرده) ذخیره می‌شود؛ همه‌ی کوئری‌های بعدی روی همین جدول کوچک، آنی‌اند.
USE Alzahra_Final_DB;

IF OBJECT_ID('dbo.Fact_Deposit_Portfolio_Monthly') IS NOT NULL
    DROP TABLE dbo.Fact_Deposit_Portfolio_Monthly;

WITH PerAccountMonth AS (
    SELECT
        dma.year_mount,
        ISNULL(da.deposit_type, N'نامشخص')     AS deposit_type,
        dma.deposit_id,
        dma.customer_id,
        SUM(dma.sum_creditor_circul_amount_eq) AS credit_amt,
        SUM(dma.sum_debtor_circul_amount_eq)   AS debit_amt,
        SUM(dma.sum_creditor_circul_count)     AS credit_cnt,
        SUM(dma.sum_debtor_circul_count)       AS debit_cnt,
        AVG(dma.avr_total_amount_eq)           AS avg_balance
    FROM dbo.Deposit_Monthly_Activity dma
    LEFT JOIN dbo.vw_Deposit_Account_Dedup da
        ON dma.deposit_id = da.deposit_id
    GROUP BY dma.year_mount, ISNULL(da.deposit_type, N'نامشخص'), dma.deposit_id, dma.customer_id
)
SELECT
    year_mount,
    deposit_type,
    COUNT(*)                        AS account_count,
    COUNT(DISTINCT customer_id)     AS customer_count,
    SUM(credit_amt)                 AS total_credit_turnover,
    SUM(debit_amt)                  AS total_debit_turnover,
    SUM(credit_cnt)                 AS credit_txn_count,
    SUM(debit_cnt)                  AS debit_txn_count,
    AVG(avg_balance)                AS avg_balance
INTO dbo.Fact_Deposit_Portfolio_Monthly
FROM PerAccountMonth
GROUP BY year_mount, deposit_type;

CREATE UNIQUE CLUSTERED INDEX PK_Fact_Deposit_Portfolio_Monthly
ON dbo.Fact_Deposit_Portfolio_Monthly (year_mount, deposit_type);

PRINT 'جدول Fact_Deposit_Portfolio_Monthly ساخته شد.';
SELECT COUNT(*) AS row_count FROM dbo.Fact_Deposit_Portfolio_Monthly;
