-- گردش کلی ماهانه‌ی هر مشتری (یک ردیف به‌ازای هر مشتری-ماه)
-- نکته‌ی حیاتی: Customer_Monthly_Activity خام یک ردیف به‌ازای هر (مشتری، ماه، کد کارمزد) دارد و ستون‌های
-- گردش کلی (sum_creditor/debtor) در همه‌ی آن ردیف‌ها عیناً تکرار شده‌اند — تأیید شد با نمونه‌برداری مستقیم.
-- بنابراین اینجا با DISTINCT دوباره به سطح «یک ردیف = یک مشتری-ماه» برگردانده می‌شود.
-- هشدار: اگر همین مقدار گردش به اشتباه هم‌زمان با کارمزدها SUM شود، عدد چند برابر (به تعداد ردیف‌های کارمزد) تورم می‌یابد.
CREATE OR ALTER VIEW dbo.vw_Customer_Turnover_Monthly AS
SELECT DISTINCT
    main_customer_id,
    year_mount,
    sum_creditor_circul_amount_eq,
    sum_debtor_circul_amount_eq,
    sum_creditor_circul_count,
    sum_debtor_circul_count
FROM dbo.Customer_Monthly_Activity;
