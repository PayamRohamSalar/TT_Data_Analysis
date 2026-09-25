-- نسخه‌ی قطعه‌قطعه (Chunked) ساخت Fact_Deposit_Portfolio_Monthly — هر ماه جدا پردازش می‌شود تا
-- Sort/Hash مجبور به Spill سنگین روی tempdb نشود (تجربه‌ی واقعی: نسخه‌ی یک‌باره روی کل جدول
-- بیش از ۴۰ دقیقه طول کشید و ۲۳ گیگ tempdb مصرف کرد؛ هر ماه به‌تنهایی ۱۲-۲۷ ثانیه بود).
USE Alzahra_Final_DB;

IF OBJECT_ID('dbo.Fact_Deposit_Portfolio_Monthly') IS NOT NULL
    DROP TABLE dbo.Fact_Deposit_Portfolio_Monthly;

CREATE TABLE dbo.Fact_Deposit_Portfolio_Monthly (
    year_mount              numeric(38,0)   NOT NULL,
    deposit_type            nvarchar(50)    NOT NULL,
    account_count           int             NOT NULL,
    customer_count          int             NOT NULL,
    total_credit_turnover   numeric(38,2),
    total_debit_turnover    numeric(38,2),
    credit_txn_count        numeric(38,0),
    debit_txn_count         numeric(38,0),
    avg_balance             numeric(38,4)
);

DECLARE @y INT = 1399;
DECLARE @m INT = 1;
DECLARE @ym INT;
DECLARE @sql NVARCHAR(MAX);

WHILE (@y < 1404) OR (@y = 1404 AND @m <= 12)
BEGIN
    SET @ym = @y * 100 + @m;

    INSERT INTO dbo.Fact_Deposit_Portfolio_Monthly
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
    FROM (
        SELECT
            dma.year_mount,
            ISNULL(da.deposit_type, N'نامشخص')     AS deposit_type,
            dma.customer_id,
            SUM(dma.sum_creditor_circul_amount_eq) AS credit_amt,
            SUM(dma.sum_debtor_circul_amount_eq)   AS debit_amt,
            SUM(dma.sum_creditor_circul_count)     AS credit_cnt,
            SUM(dma.sum_debtor_circul_count)       AS debit_cnt,
            AVG(dma.avr_total_amount_eq)           AS avg_balance
        FROM dbo.Deposit_Monthly_Activity dma
        LEFT JOIN dbo.vw_Deposit_Account_Dedup da
            ON dma.deposit_id = da.deposit_id
        WHERE dma.year_mount = @ym
        GROUP BY dma.year_mount, ISNULL(da.deposit_type, N'نامشخص'), dma.deposit_id, dma.customer_id
    ) PerAccountMonth
    GROUP BY year_mount, deposit_type;

    PRINT CONCAT('ماه ', @ym, ' پردازش شد.');

    IF @m = 12
    BEGIN
        SET @y = @y + 1;
        SET @m = 1;
    END
    ELSE
        SET @m = @m + 1;
END

CREATE UNIQUE CLUSTERED INDEX PK_Fact_Deposit_Portfolio_Monthly
ON dbo.Fact_Deposit_Portfolio_Monthly (year_mount, deposit_type);

PRINT 'همه‌ی ۷۲ ماه پردازش و ایندکس ساخته شد.';
SELECT COUNT(*) AS row_count FROM dbo.Fact_Deposit_Portfolio_Monthly;
