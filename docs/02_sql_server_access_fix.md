# رفع مشکل ورود (Login) به SQL Server محلی

## خطای مشاهده‌شده
هنگام اتصال SSMS با Windows Authentication:
```
Login failed for user 'MicrosoftAccount\p.chiniforooshan@gmail.com'. (Microsoft SQL Server, Error: 21)
Warning: Fatal error 823 occurred ...
```
همین خطا قبلاً با `sqlcmd -S localhost -E -C` هم رخ داده بود.

## علت
- حساب ویندوز فعلی (`desktop-ngqp0el\payam`) به یک Microsoft Account (`p.chiniforooshan@gmail.com`) لینک است.
- در برخی نسخه‌های ویندوز ۱۱، وقتی چنین حسابی برای احراز هویت به یک سرویس محلی (مثل SQL Server) معرفی می‌شود، به‌جای نام SAM محلی، با فرمت `MicrosoftAccount\<email>` شناخته می‌شود — که SQL Server قادر به تطبیق/احراز آن نیست.
- `Error: 21` یک خطای سطح پایین SSPI (مذاکره‌ی احراز هویت) است، نه یک رد دسترسی معمولی (که کد 18456 می‌داد) — یعنی مشکل قبل از رسیدن به بررسی مجوز رخ می‌دهد.
- بررسی شد: `LoginMode = 1` یعنی سرور فقط Windows Authentication را قبول می‌کند؛ Mixed Mode غیرفعال است، پس فعلاً راه فرار به SQL Authentication هم نداریم مگر این‌که اول یک اتصال ادمین موفق بگیریم.

## راه‌حل ۱ — امتحان سریع (ممکن است کافی باشد)
1. روی آیکون **SSMS راست‌کلیک → Run as administrator**.
2. دوباره با Windows Authentication وصل شوید.

اگر وصل شد، از **راه‌حل ۲** صرف‌نظر کنید و مستقیم بروید سراغ ریستور.

## راه‌حل ۲ — بازیابی رسمی دسترسی sysadmin (روش استاندارد مایکروسافت، از طریق SQL Server Configuration Manager)

اگر راه‌حل ۱ کار نکرد، از روش رسمی «single-user mode» استفاده می‌کنیم. این روش دقیقاً همان چیزی است که مایکروسافت برای «هیچ‌کس دسترسی sysadmin ندارد» توصیه می‌کند و کاملاً امن است — دسترسی هیچ داده‌ای تغییر نمی‌کند، فقط نقش sysadmin اضافه می‌شود.

> ⚠️ **نکته‌ی مهم (تجربه‌ی واقعی، ۲۰۲۶-۰۹-۰۳):** روش قبلی این سند (اجرای دستی `sqlservr.exe -m` از خط فرمان) باعث می‌شد سرویس با مسیرهای پیش‌فرض (نه مسیرهای واقعی پروژه روی `D:\SQLServer\...`) بالا بیاید و کار درستی از آن حاصل نشد. **روش درست و تست‌شده‌ای که واقعاً جواب داد**، اضافه‌کردن پارامتر `-m` از طریق **SQL Server Configuration Manager** است — این‌طور سرویس دقیقاً با همان تنظیمات همیشگی (و مسیرهای صحیح) فقط در حالت تک‌کاربره بالا می‌آید.

> همه‌ی دستورات PowerShell زیر باید با **دسترسی Administrator** اجرا شوند (راست‌کلیک روی PowerShell → Run as administrator).

### مرحله ۱ — افزودن پارامتر `-m` از Configuration Manager
1. در Start Menu بنویسید: **SQL Server Configuration Manager** و بازش کنید.
2. در ستون چپ روی **SQL Server Services** کلیک کنید.
3. روی **SQL Server (MSSQLSERVER)** در سمت راست، راست‌کلیک → **Properties**.
4. به تب **Startup Parameters** بروید.
5. در کادر «Specify a startup parameter»، بنویسید `-m` و دکمه‌ی **Add** را بزنید، سپس **OK / Apply**.

### مرحله ۲ — ری‌استارت سرویس (تا تنظیم تک‌کاربره واقعاً فعال شود)
```powershell
Restart-Service -Name "MSSQLSERVER" -Force
```
⚠️ فقط ذخیره‌کردن پارامتر در Configuration Manager کافی نیست — تا سرویس ری‌استارت نشود، تغییر روی سرویسِ در حال اجرا اعمال نمی‌شود.

### مرحله ۳ — در یک پنجره‌ی Administrator PowerShell **جدید** (دومی)
```powershell
sqlcmd -S localhost -E -C
```
سپس در پرامپت sqlcmd این دستورات را بزنید (بعد از هر بلوک `GO` را هم بزنید):
```sql
CREATE LOGIN [desktop-ngqp0el\payam] FROM WINDOWS;
GO
ALTER SERVER ROLE sysadmin ADD MEMBER [desktop-ngqp0el\payam];
GO
```
> اگر `CREATE LOGIN` خطای «already exists» داد، مشکلی نیست — فقط خط `ALTER SERVER ROLE ...` را اجرا کنید.

برای اطمینان بیشتر (فعال‌سازی SQL Authentication به‌عنوان مسیر پشتیبان)، همان‌جا:
```sql
EXEC xp_instance_regwrite N'HKEY_LOCAL_MACHINE', N'Software\Microsoft\MSSQLServer\MSSQLServer', N'LoginMode', REG_DWORD, 2;
GO
ALTER LOGIN sa WITH PASSWORD = N'YourStrongPassword!1';
GO
ALTER LOGIN sa ENABLE;
GO
```
> رمز `sa` را با یک رمز واقعی و قوی جایگزین کنید و آن را جایی امن (نه در گیت) یادداشت کنید — بعداً در `config/.env` پروژه هم لازم می‌شود اگر تصمیم گرفتید به‌جای Windows Auth از SQL Auth استفاده کنید.

سپس خارج شوید:
```sql
EXIT
```

### مرحله ۴ — بازگرداندن سرور به حالت عادی (چندکاربره)
1. در همان **SQL Server Configuration Manager** (مرحله ۱)، پارامتر `-m` را از تب Startup Parameters **حذف** کنید (Remove) و Apply/OK بزنید.
2. سرویس را دوباره ری‌استارت کنید:
```powershell
Restart-Service -Name "MSSQLSERVER" -Force
```
⚠️ تا این ری‌استارت انجام نشود، سرور همچنان در حالت تک‌کاربره می‌ماند و هر اتصال دومی (حتی SSMS) با خطای «Server is in single user mode» رد می‌شود.

### مرحله ۵ — تست نهایی
```powershell
sqlcmd -S localhost -E -C -Q "SELECT SUSER_SNAME(), IS_SRVROLEMEMBER('sysadmin')"
```
اگر ستون دوم مقدار `1` را نشان داد، یعنی دسترسی sysadmin برقرار شد. حالا SSMS را (بدون نیاز به Run as administrator) دوباره باز کنید و متصل شوید.

## بعد از رفع مشکل
همین‌جا (`docs/EXECUTION_LOG.md`) نتیجه ثبت خواهد شد. سپس مرحله‌ی ریستور بک‌آپ در SSMS ادامه پیدا می‌کند.
