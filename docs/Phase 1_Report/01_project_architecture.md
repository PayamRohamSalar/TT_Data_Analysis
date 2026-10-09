# معماری و اسکلت پروژه

تاریخ: 2026-08-28

## چیدمان کلی

```
TT_DataAnalysis/
├── config/                       تنظیمات اتصال و مسیرها (config.yaml بدون رمز، .env حساس و gitignore‌شده)
├── sql/
│   ├── views/                    هر View یک فایل .sql، نسخه‌بندی‌شده در git
│   ├── procedures/
│   └── adhoc/                    کوئری‌های اکتشافی یک‌بارمصرف
├── data/                          gitignore کامل — هرگز کامیت نمی‌شود
│   ├── raw/                       خروجی خام کوئری‌ها (parquet/csv)
│   ├── interim/                   داده‌ی نیمه‌پاک‌سازی‌شده
│   └── processed/                 دیتاست نهایی آماده مدل‌سازی — رابط بین فازها
├── notebooks/                     اکتشاف و گزارش‌گیری، یک پوشه به‌ازای هر فاز
│   ├── phase1_market_overview/
│   ├── phase2_clustering/
│   ├── phase3_behavior_patterns/
│   ├── phase4_prediction_models/
│   └── phase5_strategy/
├── src/tt_bank/                   پکیج پایتون نصب‌شدنی (pip install -e .)
│   ├── db/connection.py           نقطه‌ی مشترک اتصال SQLAlchemy — همه‌ی فازها از همین‌جا استفاده می‌کنند
│   ├── common/                    ابزار مشترک: پلات، لاگ، اعتبارسنجی
│   ├── phase1_overview/
│   ├── phase2_clustering/
│   ├── phase3_segmentation/
│   ├── phase4_modeling/           extract → transform → model، به‌ازای هر زیرهدف یک فایل (clv.py، default_risk.py، ...)
│   └── phase5_reporting/
├── models/                        مدل‌های سریالایز‌شده — gitignore
├── reports/figures/                خروجی گزارش/نمودار هر فاز
├── tests/                          pytest برای توابع src/ (بدون نیاز به اتصال زنده دیتابیس)
├── scripts/                        اجرای سرتاسری هر فاز (run_phase1.py و ...)
└── docs/                           همین مستندات
```

## اصول طراحی

1. **نوت‌بوک = اکتشاف، `src/` = منطق تولیدی.** هر تحلیلی که در نوت‌بوک جواب داد و قرار است دوباره استفاده شود، به `src/tt_bank/` منتقل می‌شود.
2. **SQL به‌عنوان لایه‌ی قرارداد داده.** View/Procedure در خود SQL Server ساخته می‌شوند، ولی متن آن‌ها به‌صورت فایل `.sql` در `sql/` نسخه‌بندی می‌شود تا هم مستند باشد هم قابل بازتولید روی instance دیگر.
3. **جداسازی فازها از طریق `data/processed/`، نه import مستقیم.** مثلاً خروجی خوشه‌بندی فاز ۲ به‌صورت فایل در `data/processed/` نوشته می‌شود و فاز ۳ آن را از آنجا می‌خواند — هر فاز مستقل و قابل اجرای مجدد می‌ماند.
4. **کانفیگ از کد جداست.** `config/config.yaml` (مسیرها، نام دیتابیس) commit می‌شود؛ `config/.env` (رمز عبور) هرگز commit نمی‌شود.
5. **جداسازی داده از کد در سطح فایل‌سیستم/OneDrive.** `data/` و `models/` هم از git و هم (توصیه می‌شود) از sync خودکار OneDrive مستثنی شوند چون حجیم و/یا حساس‌اند.

## پیکربندی محیط توسعه

| ابزار | نقش در این پروژه |
|---|---|
| **VS Code** | IDE اصلی — با اکستنشن‌های Python، Jupyter، **mssql** (اجرای T-SQL مستقیم از workspace) |
| **Claude Code** | درایور اصلی AI-pairing برای کدنویسی SQL/Python هم‌زمان با دسترسی به فایل‌سیستم پروژه |
| **SSMS 22** | کارهای سنگین DBA (ریستور، ایندکس، execution plan) |
| **Miniconda** (env: `tt_bank`, پایتون 3.11) | مدیریت وابستگی‌های پایتون؛ envs/pkgs روی `D:\Conda` (نه C:) |
| **Gemini CLI** | ابزار کمکی/ثانویه (مثلاً خلاصه‌سازی اسناد حجیم) — نه درایور اصلی |
| Cursor / Docker | فعلاً نصب نشده‌اند؛ در صورت نیاز آینده اضافه می‌شوند |

جزئیات کامل بستر سخت‌افزار/نرم‌افزار در [00_system_environment.md](00_system_environment.md).

## محل فایل‌ها (تفکیک مهم)

| چیز | مسیر |
|---|---|
| بک‌آپ خام `.bak` (فقط آرشیو) | `D:\TT_Bank\Alzahra_Bachup` |
| فایل‌های دیتابیس ریستورشده (MDF/LDF) | `D:\SQLServer\Data` و `D:\SQLServer\Log` (مسیر پیش‌فرض instance) |
| کد پروژه (این ریپو) | `D:\OneDrive\AI-Project\TT_DataAnalysis` |

> این ساختار در حین اجرای پروژه ممکن است کمی تغییر کند؛ نسخه‌ی به‌روز همیشه همین فایل است، نه حافظه‌ی مکالمه.
