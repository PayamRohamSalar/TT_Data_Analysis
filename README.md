# تجزیه و تحلیل رفتار مشتریان بانک توسعه تعاون

## منابع داده
- بک‌آپ خام (فقط بایگانی، دست‌نخورده): `D:\TT_Bank\Alzahra_Bachup`
- دیتابیس ریستورشده (SQL Server محلی، instance: `MSSQLSERVER`): مسیر داده در `D:\SQLServer\Data`
- نام دیتابیس و روش اتصال را در `config/config.yaml` و `config/.env` تنظیم کنید.

## فازهای پروژه
| فاز | موضوع | کد | نوت‌بوک |
|---|---|---|---|
| ۱ | بازار هدف و رفتار مشتریان (سپرده، تسهیلات، مطالبات، سود/زیان) | `src/tt_bank/phase1_overview` | `notebooks/phase1_market_overview` |
| ۲ | خوشه‌بندی مشتریان (بازه ۵ ساله) | `src/tt_bank/phase2_clustering` | `notebooks/phase2_clustering` |
| ۳ | الگوهای رفتاری به تفکیک گروه‌ها (سودآور/کلان/خرد/جغرافیا/بخش اقتصادی) | `src/tt_bank/phase3_segmentation` | `notebooks/phase3_behavior_patterns` |
| ۴ | مدل‌های پیش‌بینی (سود/زیان، نکول، CLV، گرایش مشتری) | `src/tt_bank/phase4_modeling` | `notebooks/phase4_prediction_models` |
| ۵ | یافته‌ها و راهکارهای سیاستی | `src/tt_bank/phase5_reporting` | `notebooks/phase5_strategy` |

## ساختار
```
config/     تنظیمات اتصال و مسیرها
sql/        View / Procedure / کوئری‌های اکتشافی (نسخه‌بندی‌شده)
data/       raw / interim / processed — گیت‌ایگنور شده
notebooks/  اکتشاف و گزارش‌گیری per-phase
src/tt_bank/ منطق قابل‌استفاده مجدد per-phase (نصب: pip install -e .)
models/     مدل‌های آموزش‌دیده — گیت‌ایگنور شده
reports/    خروجی نهایی گزارش هر فاز
tests/      pytest
scripts/    اجرای سرتاسری هر فاز
docs/       مستندات پروژه (از جمله گزارش بستر سیستم)
```

## راه‌اندازی محیط
```bash
conda env create -f environment.yml
conda activate tt_bank
pip install -e .
cp config/.env.example config/.env   # سپس رمز اتصال SQL را در آن وارد کنید
```

> نکته: این ساختار در حین اجرای پروژه ممکن است کمی تغییر کند؛ فقط پوشه‌های قطعی از ابتدا ساخته شده‌اند.
