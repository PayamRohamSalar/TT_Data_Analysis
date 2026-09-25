"""ابزار مشترک رسم نمودار فارسی (فونت Vazirmatn + اعداد فارسی).

⚠️ نکته‌ی مهم (کشف‌شده 2026-09-03): نسخه‌ی اول این ماژول از الگوی notebooks/phase0_sampling_design
(کتابخانه‌های arabic_reshaper + python-bidi برای reshape/راست‌به‌چپ‌کردن متن) استفاده می‌کرد. با تست مستقیم
مشخص شد در نسخه‌ی فعلی matplotlib نصب‌شده در این محیط (sate_env)، متن فارسی خام با فونت Vazirmatn
**بدون هیچ پردازشی** کاملاً درست (اتصال حروف + ترتیب راست‌به‌چپ) رندر می‌شود؛ اعمال arabic_reshaper/bidi
روی این محیط متن را خراب می‌کند (ترتیب کلمات را به چپ‌به‌راست برمی‌گرداند). پس تابع fa() دیگر هیچ
reshape/bidi انجام نمی‌دهد، فقط برای سازگاری با کد قبلی نگه داشته شده (اکنون معادل str ساده است).
اگر این پروژه به محیط/نسخه‌ی matplotlib دیگری منتقل شد و دوباره متن به‌هم‌ریخت، اول بدون هیچ پردازشی
تست کنید؛ اگر خراب بود، آن‌وقت reshape/bidi را دوباره اضافه کنید (کد قبلی در git history موجود است)."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager

FONTS_DIR = Path(__file__).resolve().parents[3] / "notebooks" / "phase0_sampling_design" / "fonts"


def setup_persian_font() -> None:
    font_path = FONTS_DIR / "Vazirmatn-Regular.ttf"
    if font_path.exists():
        font_manager.fontManager.addfont(str(font_path))
        plt.rcParams["font.family"] = "Vazirmatn"
    else:
        plt.rcParams["font.family"] = "B Nazanin"
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.autolayout"] = True


def fa(text) -> str:
    """متن فارسی را برای نمایش در matplotlib آماده می‌کند (در این محیط: بدون تغییر، رجوع به یادداشت بالا)."""
    if text is None:
        return ""
    return str(text)


def to_persian_digits(value) -> str:
    """تبدیل ارقام انگلیسی یک رشته/عدد به ارقام فارسی."""
    table = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
    return str(value).translate(table)


def fa_number(value, use_persian_digits: bool = True) -> str:
    """فرمت عدد با جداکننده‌ی هزارگان، به‌صورت اختیاری با ارقام فارسی."""
    formatted = f"{value:,.0f}" if isinstance(value, (int, float)) else str(value)
    return to_persian_digits(formatted) if use_persian_digits else formatted
