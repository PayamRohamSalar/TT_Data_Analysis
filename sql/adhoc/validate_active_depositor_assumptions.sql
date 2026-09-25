-- صحت‌سنجی فرضیات vw_Active_Depositor_Flags.sql: فرمت OPEN_DATE و آلودگی MAIN_CUSTOMER_ID
SET NOCOUNT ON;
USE Alzahra_Final_DB;

PRINT '=== آیا OPEN_DATE کوتیشن دارد؟ ===';
SELECT TOP 5 OPEN_DATE, LEN(OPEN_DATE) AS len FROM Deposit_Accoutnt_Info WHERE OPEN_DATE LIKE '"%';
SELECT COUNT(*) AS quoted_count FROM Deposit_Accoutnt_Info WHERE OPEN_DATE LIKE '"%';
SELECT COUNT(*) AS total FROM Deposit_Accoutnt_Info;

PRINT '=== آیا همه‌ی OPEN_DATE فرمت دقیق YYYY/MM/DD دارند؟ (بررسی کاراکتر پنجم) ===';
SELECT SUBSTRING(LTRIM(RTRIM(REPLACE(OPEN_DATE,CHAR(34),''))), 5, 1) AS sep_char, COUNT(*) AS cnt
FROM Deposit_Accoutnt_Info
GROUP BY SUBSTRING(LTRIM(RTRIM(REPLACE(OPEN_DATE,CHAR(34),''))), 5, 1)
ORDER BY cnt DESC;

PRINT '=== آیا MAIN_CUSTOMER_ID کوتیشن یا کاراکتر غیرعددی دارد؟ ===';
SELECT COUNT(*) AS quoted_count FROM Deposit_Accoutnt_Info WHERE MAIN_CUSTOMER_ID LIKE '"%';
SELECT TOP 5 MAIN_CUSTOMER_ID FROM Deposit_Accoutnt_Info WHERE ISNUMERIC(LTRIM(RTRIM(MAIN_CUSTOMER_ID))) = 0;
SELECT COUNT(*) AS non_numeric_count FROM Deposit_Accoutnt_Info WHERE ISNUMERIC(LTRIM(RTRIM(MAIN_CUSTOMER_ID))) = 0;

PRINT '=== نمونه از OPEN_DATE های غیرمعمول (اگر سال خارج از بازه‌ی منطقی 1380-1405 باشد) ===';
SELECT TOP 10 OPEN_DATE FROM Deposit_Accoutnt_Info
WHERE ISNUMERIC(LEFT(LTRIM(RTRIM(REPLACE(OPEN_DATE,CHAR(34),''))),4))=1
  AND (CAST(LEFT(LTRIM(RTRIM(REPLACE(OPEN_DATE,CHAR(34),''))),4) AS INT) < 1380
       OR CAST(LEFT(LTRIM(RTRIM(REPLACE(OPEN_DATE,CHAR(34),''))),4) AS INT) > 1405);
SELECT COUNT(*) AS null_or_blank_open_date FROM Deposit_Accoutnt_Info WHERE OPEN_DATE IS NULL OR LTRIM(RTRIM(OPEN_DATE)) = '';
