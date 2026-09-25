-- درآمد سود دریافتی از تسهیلات (اصل+سود+جریمه به‌تفکیک)، بر اساس تاریخ پرداخت واقعی قسط — ورودی سود و زیان فاز ۱
-- ماه از payed_date (متن شمسی YYYY/MM/DD) استخراج می‌شود، نه از یک ستون ماه مجزا (این جدول چنین ستونی ندارد)
CREATE OR ALTER VIEW dbo.vw_Loan_Interest_Income_Monthly AS
SELECT
    CAST(REPLACE(LEFT(LTRIM(RTRIM(REPLACE(REPLACE(REPLACE(lma.payed_date, CHAR(34), ''), CHAR(13), ''), CHAR(10), ''))), 7), '/', '') AS int) AS year_month,
    LTRIM(RTRIM(REPLACE(lma.Status, CHAR(34), ''))) AS installment_status,  -- Status خام با کوتیشن احاطه شده: '"Jari"'
    COUNT(*)                                    AS installment_count,
    SUM(lma.installment_main)                   AS total_principal_paid,
    SUM(lma.installment_interest)               AS total_interest_paid,
    SUM(lma.installment_penalty)                AS total_penalty_paid
FROM dbo.Loan_Monthly_Activity lma
WHERE lma.payed_date IS NOT NULL AND LEN(LTRIM(RTRIM(lma.payed_date))) >= 7
GROUP BY
    CAST(REPLACE(LEFT(LTRIM(RTRIM(REPLACE(REPLACE(REPLACE(lma.payed_date, CHAR(34), ''), CHAR(13), ''), CHAR(10), ''))), 7), '/', '') AS int),
    LTRIM(RTRIM(REPLACE(lma.Status, CHAR(34), '')));
