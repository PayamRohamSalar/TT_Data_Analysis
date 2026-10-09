# گزارش بستر سیستم و محیط توسعه — پروژه TT_DataAnalysis

تاریخ بررسی: 2026-08-28

## ۱. مشخصات سخت‌افزاری

| مورد | مقدار |
|---|---|
| مدل | ASUS TUF (لپ‌تاپ) |
| CPU | Intel Core i7-14650HX — 16 هسته فیزیکی / 24 رشته منطقی |
| RAM | 31.6 GB (نصب‌شده به‌عنوان 32GB DDR5) |
| GPU (اعلامی) | RTX 5060 |
| GPU (شناسایی‌شده توسط ویندوز) | **فقط Intel(R) UHD Graphics** — کارت گرافیک RTX در `Win32_VideoController` دیده نشد |
| ذخیره‌سازی کل | ~1TB روی سه درایو منطقی (جدول زیر) |

> ✅ **به‌روزرسانی 2026-08-28 (بعدازظهر):** علت اصلی، حالت **Eco Mode در ASUS Armoury Crate** بود که GPU گسسته را کاملاً خاموش نگه می‌داشت. کاربر آن را به حالت **Standard** تغییر داد و اکنون کارت به‌طور کامل شناسایی می‌شود:
> - `NVIDIA GeForce RTX 5060 Laptop GPU` — 8GB VRAM، درایور 591.91، **CUDA 13.1**
> - `nvidia-smi` طبیعی کار می‌کند.
>
> **مشکل جداگانه‌ی Ollama نیز پیدا و رفع شد:** کرش‌لوپ Ollama ربطی به GPU نداشت؛ پورت پیش‌فرض آن (`11434`) داخل یک بازه‌ی رزروشده توسط ویندوز (`netsh int ipv4 show excludedportrange`, احتمالاً به‌خاطر WSL2/Hyper-V) بود و bind کردن آن پورت با خطای "دسترسی ممنوع" رد می‌شد. با تنظیم `OLLAMA_HOST=127.0.0.1:12434` (پورت خارج از بازه‌های رزرو) سرویس بالا آمد و تست inference روی مدل `qwen2.5-coder:1.5b` اجرا شد؛ در حین اجرا `nvidia-smi` مصرف GPU (~15% util, ~2.1GB VRAM) را نشان داد — یعنی **Ollama از GPU به‌درستی استفاده می‌کند**.
>
> **کاری که کاربر باید انجام دهد تا این تنظیم دائمی شود:** یک متغیر محیط کاربر (User Environment Variable) با نام `OLLAMA_HOST` و مقدار `127.0.0.1:12434` تعریف کند (Settings → System → About → Advanced system settings → Environment Variables)، سپس اپ Ollama را ری‌استارت کند. مدل‌های موجود از قبل روی سیستم: `qwen2.5-coder:1.5b` (986MB) و `qwen2.5-coder:7b` (4.7GB).
>
> <details><summary>یادداشت قدیمی (قبل از تغییر Eco Mode) — صرفاً برای تاریخچه</summary>
>
> کارت RTX 5060 در آن زمان **اصلاً توسط ویندوز شناسایی نمی‌شد** — نه در GPUهای فعال (`Win32_VideoController`) و نه در لیست کامل دستگاه‌های PnP کلاس Display (فقط `Intel(R) UHD Graphics — Status: OK` دیده می‌شود، هیچ دستگاه غیرفعال/Problem هم نیست). `nvidia-smi` با خطای دسترسی مواجه شد نه خطای "not found"، که با شناسایی‌نشدن کارت در PnP همخوانی ندارد و نشان می‌دهد درایور NVIDIA اصلاً نصب نیست. علاوه بر این، هنگام تست Ollama، سرویس آن وارد یک **حلقه کرش پیوسته** شد (`ollama exited: exit status 1`, بارها در ثانیه) که به احتمال زیاد به همین نبود درایور/GPU مرتبط است؛ این پردازش‌ها را متوقف کردم تا منابع سیستم هدر نرود.
>
> **جمع‌بندی:** برای استفاده از GPU (چه برای Ollama محلی، چه برای آموزش مدل با PyTorch/XGBoost-GPU در فاز ۴) باید:
> 1. درایور NVIDIA (GeForce یا Studio) از سایت رسمی نصب شود.
> 2. تنظیم گرافیک هیبریدی (MUX Switch / Optimus) در BIOS و NVIDIA Control Panel بررسی شود.
> 3. بعد از نصب درایور، Ollama را دوباره تست کنیم.
>
> تا آن زمان، فرض می‌کنیم پردازش‌ها روی CPU (16 هسته) انجام می‌شود — که برای فازهای ۱ تا ۳ (SQL، EDA، خوشه‌بندی کلاسیک) کاملاً کافی است؛ فقط برای مدل‌های سنگین یادگیری عمیق در فاز ۴ اهمیت پیدا می‌کند.
>
> </details>

## ۲. ساختار درایوها

| درایو | برچسب | حجم کل | فضای آزاد | کاربرد |
|---|---|---|---|---|
| C: | — | 300 GB | 154.5 GB | ویندوز، Program Files، `C:\SQL2025` |
| D: | Projects | 300 GB | 260.2 GB | پروژه‌ها، Conda، داده بانک، SQL Server Data |
| E: | Archive/Media | 352.9 GB | 253.9 GB | آرشیو رسانه (فیلم/سریال) — بی‌ربط به پروژه |

### ساختار کلیدی روی D:\

```
D:\
├── AI\
│   └── OllamaModels\              # مدل‌های Ollama
├── Conda\
│   ├── envs\                      # محیط‌های conda (envs_dirs سفارشی)
│   │   └── sate_env\               # یک env موجود، Python 3.11.15 (نامرتبط به این پروژه)
│   └── pkgs\                      # کش پکیج‌های conda
├── OneDrive\
│   └── AI-Project\
│       └── TT_DataAnalysis\        # ← دایرکتوری کاری فعلی پروژه ما
├── Programs Sources\               # نصب‌کننده‌های دانلودشده (Installers/IDEs/DataBase/...)
├── SQLServer\                      # مسیر داده SQL Server (جدا از C:) 
│   ├── Backup\
│   ├── Data\
│   ├── Log\
│   ├── MSSQL17.MSSQLSERVER\
│   └── TempDB\
└── TT_Bank\
    └── Alzahra_Bachup               # فایل بک‌آپ خام بانک (9.55 GB, فرمت MSSQLBAK)
```

نکات مثبت این چیدمان:
- مسیر داده SQL Server عمداً به `D:\SQLServer` منتقل شده (نه C: پیش‌فرض) — درست برای جلوگیری از پرشدن درایو سیستم با دیتابیس‌های حجیم.
- `.condarc` کاربر (`C:\Users\Payam\.condarc`) هم `envs_dirs` و `pkgs_dirs` conda را به `D:\Conda` هدایت کرده — همین منطق درست، برای جلوگیری از تورم C:.
- پروژه در OneDrive (`D:\OneDrive\AI-Project\TT_DataAnalysis`) قرار دارد → همگام‌سازی/بک‌آپ خودکار کد، اما باید مراقب سینک فایل‌های حجیم (دیتاست‌های خروجی، مدل‌های آموزش‌دیده) بود؛ این‌ها باید در `.gitignore`/خارج از دامنه sync OneDrive نگه داشته شوند.

## ۳. پایگاه‌داده

| مورد | مقدار |
|---|---|
| SQL Server | نصب شده (سرویس `MSSQLSERVER` در حال اجرا)، نسخه پوشه: `MSSQL17.MSSQLSERVER` (SQL Server 2025) |
| مسیر داده/لاگ/بک‌آپ | همگی روی `D:\SQLServer\*` |
| SSMS | **SQL Server Management Studio 22** — نصب‌شده در `C:\Program Files\...` (تاریخ نصب: همین اواخر) |
| فایل بک‌آپ خام | `D:\TT_Bank\Alzahra_Bachup` — فرمت native `.bak` (هدر `MSSQLBAK`)، حجم 9.55GB |
| وضعیت دسترسی | حساب ویندوز فعلی (`desktop-ngqp0el\payam`) هنوز روی instance محلی sysadmin نیست (login failed در تست اولیه) — نیاز به تنظیم دسترسی در SSMS |

## ۴. محیط توسعه و ابزارها

| ابزار | وضعیت | نسخه/مسیر |
|---|---|---|
| VS Code | ✅ نصب | 1.134.0 — `AppData\Local\Programs\Microsoft VS Code` |
| Cursor | ⚠️ **فقط installer موجود است، نصب نشده** | فایل `CursorUserSetup-x64-3.16.17.exe` در `D:\Programs Sources\IDEs`، اما پوشه نصب یافت نشد |
| Miniconda | ✅ نصب (پایه) | py314_26.5.3-2 (Python 3.14.6) — envs/pkgs روی D: |
| Conda env موجود | `sate_env` (Python 3.11.15) — برای این پروژه env جدید می‌سازیم |
| Git | ✅ نصب | 2.55.0.windows.4 |
| Node.js / npm | ✅ نصب | Node v24.20.0 / npm 11.19.0 |
| Ollama | ✅ نصب، در حال بررسی سرویس/مدل‌ها | client 0.32.15 — مدل‌ها در `D:\AI\OllamaModels` |
| Gemini CLI | ✅ نصب (از طریق npm) | 0.57.0 |
| Docker | ❌ **نصب نیست** | نه در Program Files، نه در رجیستری — کاربر گفته بود پیکربندی شده، اما فعلاً یافت نشد |
| WSL2 | ✅ فعال | Distro پیش‌فرض: Ubuntu، WSL2 |
| GapGPT / MindsHub Cowork | نصب‌شده (ابزارهای جانبی مرتبط با AI) | `AppData\Local\Programs\` |

### ناهماهنگی‌هایی که باید روشن شوند
1. **Docker** در سیستم نصب نیست (نه Docker Desktop، نه در رجیستری دیده شد). اگر برای فازهای بعدی (مثلاً سرو کردن مدل یا containerize کردن پایپ‌لاین) لازم است، باید نصب شود.
2. **Cursor** فقط installer آن دانلود شده ولی نصب نشده.
3. ~~RTX 5060 شناسایی نمی‌شد~~ — **حل شد**: علت Eco Mode در Armoury Crate بود؛ با تغییر به Standard Mode کارت کاملاً شناسایی شد و Ollama با تنظیم `OLLAMA_HOST` روی پورت جایگزین، از GPU استفاده می‌کند (جزئیات در بخش ۱).

---
*این گزارش با اسکن مستقیم سیستم تهیه شده (drive layout، رجیستری نصب برنامه‌ها، نسخه ابزارهای CLI، دستگاه‌های PnP).*
