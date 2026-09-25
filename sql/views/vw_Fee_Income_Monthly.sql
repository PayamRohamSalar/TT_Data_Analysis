-- درآمد کارمزدی بانک به تفکیک کد کارمزد و ماه — ورودی محاسبه‌ی سود و زیان فاز ۱
-- ایمن از نظر تجمیع: هر ردیف Customer_Monthly_Activity یک شارژ کارمزد واقعی است (SUM مستقیم صحیح است)
-- code/title خام با کوتیشن احاطه شده‌اند: '"2423"', '"کارمزد ..."'
CREATE OR ALTER VIEW dbo.vw_Fee_Income_Monthly AS
SELECT
    cma.year_mount,
    LTRIM(RTRIM(REPLACE(cma.code, CHAR(34), '')))   AS fee_code,
    LTRIM(RTRIM(REPLACE(cma.title, CHAR(34), '')))  AS fee_title,
    COUNT(*)                 AS charge_count,
    COUNT(DISTINCT cma.main_customer_id) AS customer_count,
    SUM(cma.amount_eq)       AS total_amount
FROM dbo.Customer_Monthly_Activity cma
WHERE cma.code IS NOT NULL
GROUP BY cma.year_mount, LTRIM(RTRIM(REPLACE(cma.code, CHAR(34), ''))), LTRIM(RTRIM(REPLACE(cma.title, CHAR(34), '')));
