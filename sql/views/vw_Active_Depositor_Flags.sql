-- پرچم «سپرده‌گذار فعال» بر اساس معیارهای RFM مستندشده در docs/07_sampling_methodology.md (بخش ۲)
-- منطق AND (سناریوی محافظه‌کارانه گزارش نمونه‌گیری): مشتری باید هر ۴ شرط را همزمان داشته باشد.
-- گرین (Grain): یک ردیف به‌ازای هر customer_id (سپرده‌گذار)
--
-- ✅ صحت‌سنجی شد (نشست Claude Code بومی، 2026-08-30) — جزئیات کامل در docs/08_data_landscape_report.md:
--   - فرمت OPEN_DATE: همه‌ی ۱,۵۲۲,۹۷۱ ردیف دقیقاً 'YYYY/MM/DD' هستند (کاراکتر پنجم همیشه '/')، بدون کوتیشن/CHAR(34).
--   - MAIN_CUSTOMER_ID: بدون کوتیشن، ۱۰۰٪ عددی.
--   - ⚠️ فقط ۶۹ ردیف (۳۵ مشتری) مقدار ساختگی '1300/01/01' دارند (تاریخ پیش‌فرض سیستم بانک) — حجم نادیده‌گرفتنی.
--
-- 🐛 باگ ساختاری رفع‌شده (نشست Claude Code بومی، 2026-08-30): نسخه‌ی اول Recency/Frequency را از
-- vw_Customer_Turnover_Monthly (مبتنی بر Customer_Monthly_Activity) می‌گرفت. آن جدول فقط ۳۲۸,۷۸۹ مشتری
-- یکتا دارد، در حالی‌که جمعیت واقعی سپرده‌گذاران (Deposit_Accoutnt_Info) ۷۰۶,۵۰۹ نفر است — یعنی ۵۳٪ از
-- سپرده‌گذاران اصلاً در جمعیت پایه‌ی View دیده نمی‌شدند (Sanity Check این را آشکار کرد: عدد فعال محاسبه‌شده
-- ۶ برابر کوچک‌تر از گزارش نمونه‌گیری بود). راه‌حل: Recency/Frequency حالا مستقیماً از Deposit_Monthly_Activity
-- محاسبه می‌شود (همان منبع Monetary)، نه از جدول فعالیت کلی مشتری — هم پوشش کامل می‌دهد، هم به لحاظ مفهومی
-- درست‌تر است (رفتار سپرده‌ای، نه فعالیت کارمزدی کل مشتری).
--
-- فرضیات این نسخه:
--   - "ماه آخر داده" = 140412 (اسفند ۱۴۰۴)، طبق docs/03_data_dictionary.md. اگر داده به‌روزتر شد، این عدد باید پویا محاسبه شود.
--   - Recency: حداقل یک تراکنش (گردش بستانکار یا بدهکار) در ۶ ماه اخیر، یعنی year_mount >= 140407.
--   - Frequency: حداقل ۱ ماه با گردش غیرصفر در کل ۷۱ ماه.
--   - Monetary-Deposit: حداکثر مانده‌ی میانگین ماهانه (روی مجموع حساب‌های سپرده‌ی مشتری) طی کل دوره >= 5,000,000 ریال.
--   - Tenure: OPEN_DATE با فرمت متنی شمسی 'YYYY/MM/DD' است؛ قدمت با پارس رشته‌ای ساده (سال×۱۲+ماه) نسبت به 1404/12 محاسبه می‌شود.
--   - جمعیت پایه: اتحاد مشتریان Deposit_Monthly_Activity و Deposit_Accoutnt_Info (کسی که حداقل یک حساب سپرده دارد).

CREATE OR ALTER VIEW dbo.vw_Active_Depositor_Flags AS
WITH DepositBase AS (
    -- جمعیت کامل سپرده‌گذاران: هر کسی که حداقل یک حساب سپرده دارد (نه فقط کسی که گردش ماهانه ثبت کرده)
    SELECT DISTINCT CAST(LTRIM(RTRIM(MAIN_CUSTOMER_ID)) AS numeric(38,0)) AS customer_id
    FROM dbo.Deposit_Accoutnt_Info
    WHERE ISNUMERIC(LTRIM(RTRIM(MAIN_CUSTOMER_ID))) = 1
),
DepositMonthly AS (
    SELECT customer_id, year_mount,
           SUM(avr_total_amount_eq)        AS customer_month_balance,
           MAX(CASE WHEN sum_creditor_circul_count > 0 OR sum_debtor_circul_count > 0 THEN 1 ELSE 0 END) AS month_has_turnover
    FROM dbo.Deposit_Monthly_Activity
    GROUP BY customer_id, year_mount
),
RecencyFrequency AS (
    SELECT
        customer_id,
        SUM(month_has_turnover) AS active_months_count,
        MAX(CASE WHEN year_mount >= 140407 AND month_has_turnover = 1 THEN 1 ELSE 0 END) AS is_recent
    FROM DepositMonthly
    GROUP BY customer_id
),
MaxBalance AS (
    SELECT customer_id, MAX(customer_month_balance) AS max_balance
    FROM DepositMonthly
    GROUP BY customer_id
),
Tenure AS (
    -- قدمت بر اساس اولین حساب سپرده‌ی افتتاح‌شده
    SELECT
        CAST(LTRIM(RTRIM(MAIN_CUSTOMER_ID)) AS numeric(38,0)) AS customer_id,
        MIN(
            (1404 - CAST(LEFT(LTRIM(RTRIM(OPEN_DATE)), 4) AS INT)) * 12
            + (12 - CAST(SUBSTRING(LTRIM(RTRIM(OPEN_DATE)), 6, 2) AS INT))
        ) AS tenure_months
    FROM dbo.Deposit_Accoutnt_Info
    WHERE ISNUMERIC(LEFT(LTRIM(RTRIM(OPEN_DATE)), 4)) = 1
      AND ISNUMERIC(LTRIM(RTRIM(MAIN_CUSTOMER_ID))) = 1
    GROUP BY LTRIM(RTRIM(MAIN_CUSTOMER_ID))
)
SELECT
    b.customer_id,
    ISNULL(rf.is_recent, 0)             AS is_recent,
    ISNULL(rf.active_months_count, 0)   AS active_months_count,
    mb.max_balance,
    t.tenure_months,
    CASE WHEN ISNULL(rf.is_recent, 0) = 1
              AND ISNULL(rf.active_months_count, 0) >= 1
              AND mb.max_balance >= 5000000
              AND t.tenure_months >= 12
         THEN 1 ELSE 0 END              AS is_active_depositor
FROM DepositBase b
LEFT JOIN RecencyFrequency rf ON rf.customer_id = b.customer_id
LEFT JOIN MaxBalance mb       ON mb.customer_id = b.customer_id
LEFT JOIN Tenure t             ON t.customer_id  = b.customer_id;
