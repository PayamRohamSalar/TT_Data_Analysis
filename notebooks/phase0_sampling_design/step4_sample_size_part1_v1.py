# -*- coding: utf-8 -*-
"""
مرحله ۴: محاسبه حجم نمونه و طراحی استراتژی نمونه‌گیری
پروژه: تحلیل رفتار مشتریان بانک توسعه تعاون
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import font_manager
from pathlib import Path

# --- مسیرها (اصلاح‌شده هنگام انتقال به TT_DataAnalysis، ۲۰۲۶-۰۸-۲۹) ---
# کد اصلی از D:\OneDrive\AI-Project\Tosee_Taavon منتقل شده؛ مسیرهای مطلق ویندوزی
# با مسیرهای نسبی به ریشه‌ی این پروژه جایگزین شدند.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW_DIR = PROJECT_ROOT / 'data' / 'raw' / 'phase0_sampling_design'
DATA_PROCESSED_DIR = PROJECT_ROOT / 'data' / 'processed' / 'phase0_sampling_design'
FIGURES_DIR = PROJECT_ROOT / 'reports' / 'figures' / 'phase0_sampling_design'
FONTS_DIR = Path(__file__).resolve().parent / 'fonts'
# --- پایان بخش مسیرها ---

import warnings
warnings.filterwarnings('ignore')

# کتابخانه‌های فارسی
import arabic_reshaper
from bidi.algorithm import get_display

# ==============================================================================
# Font Configuration
# ==============================================================================

import matplotlib
matplotlib.use('Agg')

font_path = FONTS_DIR / 'Vazirmatn-Regular.ttf'

# پاک کردن کش فونت‌ها (در صورت وجود)
import matplotlib.font_manager as fm
try:
    # تلاش برای بازسازی کش فونت (ممکن است در برخی نسخه‌ها موجود نباشد)
    if hasattr(fm, '_rebuild'):
        fm._rebuild()
except (AttributeError, Exception):
    # اگر متد موجود نباشد، ادامه می‌دهیم
    pass

if font_path.exists():
    fm.fontManager.addfont(str(font_path))
    plt.rcParams['font.family'] = 'Vazirmatn'
    print("✓ فونت Vazirmatn بارگذاری شد")
else:
    print("⚠ فونت Vazirmatn یافت نشد، از B Nazanin استفاده می‌شود")
    plt.rcParams['font.family'] = 'B Nazanin'

plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.autolayout'] = True
plt.rcParams['font.size'] = 11

# ==============================================================================
# Helper Functions
# ==============================================================================

def fix_persian_text(text):
    if text is None or str(text).strip() == '':
        return ''
    try:
        reshaped_text = arabic_reshaper.reshape(str(text))
        bidi_text = get_display(reshaped_text)
        return bidi_text
    except Exception as e:
        return str(text)

def convert_to_persian_number(number):
    english_digits = '0123456789'
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    translation_table = str.maketrans(english_digits, persian_digits)
    return str(number).translate(translation_table)

def format_number_with_separator(number, use_persian=True):
    formatted = f'{number:,.0f}' if isinstance(number, (int, float)) else str(number)
    if use_persian:
        return convert_to_persian_number(formatted)
    return formatted

# ==============================================================================
# Setup Paths
# ==============================================================================

analysis_dir = FIGURES_DIR / 'analysis'
output_dir = FIGURES_DIR / 'sample_size' / 'v1'
output_dir.mkdir(exist_ok=True, parents=True)

print("="*80)
print("مرحله ۴: محاسبه حجم نمونه و طراحی استراتژی نمونه‌گیری")
print("="*80)
print(f"\n📁 مسیر خروجی: {output_dir}")

# ==============================================================================
# 1. بارگذاری تخمین جمعیت هدف
# ==============================================================================

print("\n" + "="*80)
print("📊 بارگذاری تخمین جمعیت هدف")
print("="*80)

population_file = analysis_dir / 'table_population_estimates.xlsx'
df_population = pd.read_excel(population_file)

print("\n" + df_population.to_string(index=False))

# استخراج اعداد (حذف درصدها و کاما)
def extract_number(text):
    """استخراج عدد از رشته مانند '1,625,242 (22.8%)'"""
    if isinstance(text, str):
        # حذف همه چیز بعد از فاصله اول و حذف کاما
        return int(text.split()[0].replace(',', ''))
    return int(text)

# تخمین محافظه‌کارانه
conservative_real = extract_number(df_population.loc[0, 'مشتریان حقیقی'])
conservative_legal = extract_number(df_population.loc[0, 'مشتریان حقوقی'])
conservative_total = conservative_real + conservative_legal

# تخمین خوش‌بینانه
optimistic_real = extract_number(df_population.loc[1, 'مشتریان حقیقی'])
optimistic_legal = extract_number(df_population.loc[1, 'مشتریان حقوقی'])
optimistic_total = optimistic_real + optimistic_legal

print(f"\n📌 تخمین محافظه‌کارانه:")
print(f"   حقیقی: {conservative_real:,}")
print(f"   حقوقی: {conservative_legal:,}")
print(f"   جمع: {conservative_total:,}")

print(f"\n📌 تخمین خوش‌بینانه:")
print(f"   حقیقی: {optimistic_real:,}")
print(f"   حقوقی: {optimistic_legal:,}")
print(f"   جمع: {optimistic_total:,}")

# ==============================================================================
# 2. پارامترهای فرمول Cochran
# ==============================================================================

print("\n" + "="*80)
print("📊 پارامترهای محاسبه حجم نمونه")
print("="*80)

# پارامترها بر اساس مستندات پروژه
Z = 2.58          # سطح اطمینان 99%
e = 0.01          # خطای مجاز 1%
p = 0.5           # نسبت جمعیت (محافظه‌کارانه‌ترین حالت)
q = 1 - p         # 0.5
DEFF = 2.0        # Design Effect (ضریب طراحی)
NR = 1.1          # Non-Response Rate (نرخ عدم پاسخ‌دهی 10%)

print(f"\n📌 پارامترهای فرمول:")
print(f"   Z (سطح اطمینان 99%): {Z}")
print(f"   e (خطای مجاز): {e} ({e*100}%)")
print(f"   p (نسبت جمعیت): {p}")
print(f"   q (1-p): {q}")
print(f"   DEFF (ضریب طراحی): {DEFF}")
print(f"   NR (نرخ عدم پاسخ‌دهی): {NR} ({(NR-1)*100}%)")

# ==============================================================================
# 3. محاسبه حجم نمونه - فرمول Cochran
# ==============================================================================

print("\n" + "="*80)
print("📊 محاسبه حجم نمونه با فرمول Cochran")
print("="*80)

def calculate_sample_size(N, Z=2.58, e=0.01, p=0.5, DEFF=2.0, NR=1.1):
    """
    محاسبه حجم نمونه با فرمول Cochran و اصلاحات
    
    n0 = (Z^2 * p * q) / e^2  (فرمول اولیه)
    n = n0 / (1 + (n0-1)/N)   (تصحیح جمعیت محدود)
    n_final = n * DEFF * NR   (اعمال ضرایب)
    """
    q = 1 - p
    
    # مرحله 1: حجم نمونه اولیه (جمعیت نامحدود)
    n0 = (Z**2 * p * q) / (e**2)
    
    # مرحله 2: تصحیح برای جمعیت محدود
    n_adjusted = n0 / (1 + ((n0 - 1) / N))
    
    # مرحله 3: اعمال ضریب طراحی و عدم پاسخ‌دهی
    n_final = n_adjusted * DEFF * NR
    
    return {
        'n0': int(np.ceil(n0)),
        'n_adjusted': int(np.ceil(n_adjusted)),
        'n_final': int(np.ceil(n_final))
    }

# محاسبه برای سناریو محافظه‌کارانه
print(f"\n📊 سناریو محافظه‌کارانه (N = {conservative_total:,}):")
sample_conservative = calculate_sample_size(conservative_total, Z, e, p, DEFF, NR)
print(f"   n₀ (اولیه): {sample_conservative['n0']:,}")
print(f"   n (تصحیح شده): {sample_conservative['n_adjusted']:,}")
print(f"   n (نهایی): {sample_conservative['n_final']:,}")

# محاسبه برای سناریو خوش‌بینانه
print(f"\n📊 سناریو خوش‌بینانه (N = {optimistic_total:,}):")
sample_optimistic = calculate_sample_size(optimistic_total, Z, e, p, DEFF, NR)
print(f"   n₀ (اولیه): {sample_optimistic['n0']:,}")
print(f"   n (تصحیح شده): {sample_optimistic['n_adjusted']:,}")
print(f"   n (نهایی): {sample_optimistic['n_final']:,}")

# ==============================================================================
# 4. تخصیص نمونه به طبقات (Proportional Allocation)
# ==============================================================================

print("\n" + "="*80)
print("📊 تخصیص نمونه به طبقات")
print("="*80)

def allocate_sample_proportional(n_total, N_real, N_legal):
    """تخصیص متناسب نمونه به حقیقی و حقوقی"""
    N_total = N_real + N_legal
    
    # نسبت هر طبقه
    ratio_real = N_real / N_total
    ratio_legal = N_legal / N_total
    
    # تخصیص نمونه
    n_real = int(np.ceil(n_total * ratio_real))
    n_legal = int(np.ceil(n_total * ratio_legal))
    
    # تعدیل برای رسیدن به جمع دقیق
    total_allocated = n_real + n_legal
    if total_allocated != n_total:
        diff = n_total - total_allocated
        # اضافه کردن تفاوت به طبقه بزرگتر
        if ratio_real > ratio_legal:
            n_real += diff
        else:
            n_legal += diff
    
    return n_real, n_legal

# تخصیص برای سناریو محافظه‌کارانه
n_conservative_real, n_conservative_legal = allocate_sample_proportional(
    sample_conservative['n_final'], conservative_real, conservative_legal)

print(f"\n📊 تخصیص سناریو محافظه‌کارانه:")
print(f"   نمونه حقیقی: {n_conservative_real:,} ({n_conservative_real/sample_conservative['n_final']*100:.1f}%)")
print(f"   نمونه حقوقی: {n_conservative_legal:,} ({n_conservative_legal/sample_conservative['n_final']*100:.1f}%)")
print(f"   جمع: {n_conservative_real + n_conservative_legal:,}")

# تخصیص برای سناریو خوش‌بینانه
n_optimistic_real, n_optimistic_legal = allocate_sample_proportional(
    sample_optimistic['n_final'], optimistic_real, optimistic_legal)

print(f"\n📊 تخصیص سناریو خوش‌بینانه:")
print(f"   نمونه حقیقی: {n_optimistic_real:,} ({n_optimistic_real/sample_optimistic['n_final']*100:.1f}%)")
print(f"   نمونه حقوقی: {n_optimistic_legal:,} ({n_optimistic_legal/sample_optimistic['n_final']*100:.1f}%)")
print(f"   جمع: {n_optimistic_real + n_optimistic_legal:,}")

# ==============================================================================
# 5. ایجاد جدول خلاصه حجم نمونه
# ==============================================================================

print("\n" + "="*80)
print("📊 جدول خلاصه حجم نمونه")
print("="*80)

sample_summary_data = {
    'سناریو': ['محافظه‌کارانه', 'خوش‌بینانه'],
    'جمعیت هدف (N)': [
        f'{conservative_total:,}',
        f'{optimistic_total:,}'
    ],
    'حجم نمونه اولیه (n₀)': [
        f'{sample_conservative["n0"]:,}',
        f'{sample_optimistic["n0"]:,}'
    ],
    'حجم نمونه تصحیح شده': [
        f'{sample_conservative["n_adjusted"]:,}',
        f'{sample_optimistic["n_adjusted"]:,}'
    ],
    'حجم نمونه نهایی': [
        f'{sample_conservative["n_final"]:,}',
        f'{sample_optimistic["n_final"]:,}'
    ],
    'نمونه حقیقی': [
        f'{n_conservative_real:,}',
        f'{n_optimistic_real:,}'
    ],
    'نمونه حقوقی': [
        f'{n_conservative_legal:,}',
        f'{n_optimistic_legal:,}'
    ]
}

df_sample_summary = pd.DataFrame(sample_summary_data)
print("\n")
print(df_sample_summary.to_string(index=False))

# ذخیره جدول
summary_file = output_dir / 'table_sample_size_summary.xlsx'
df_sample_summary.to_excel(summary_file, index=False)
print(f"\n✓ جدول ذخیره شد: {summary_file}")

# ==============================================================================
# 6. جدول تفصیلی پارامترها
# ==============================================================================

parameters_data = {
    'پارامتر': [
        'سطح اطمینان',
        'Z-Score',
        'خطای مجاز (e)',
        'نسبت جمعیت (p)',
        'ضریب طراحی (DEFF)',
        'نرخ عدم پاسخ‌دهی (NR)'
    ],
    'مقدار': [
        '99%',
        f'{Z}',
        f'{e} (1%)',
        f'{p}',
        f'{DEFF}',
        f'{NR} (10%)'
    ],
    'توضیحات': [
        'بالاترین سطح اطمینان برای دقت بالا',
        'مقدار استاندارد برای 99%',
        'حداکثر خطای مجاز در برآورد',
        'محافظه‌کارانه‌ترین حالت (حداکثر واریانس)',
        'اثر طراحی نمونه‌گیری طبقه‌بندی شده',
        'احتمال 10% عدم پاسخ‌دهی'
    ]
}

df_parameters = pd.DataFrame(parameters_data)
print("\n📋 جدول پارامترهای محاسبه:")
print(df_parameters.to_string(index=False))

# ذخیره
params_file = output_dir / 'table_sampling_parameters.xlsx'
df_parameters.to_excel(params_file, index=False)
print(f"\n✓ جدول ذخیره شد: {params_file}")

# ==============================================================================
# ادامه در بخش بعدی (نمودارها)...
# ==============================================================================

print("\n" + "="*80)
print("✅ مرحله ۴ - بخش اول کامل شد!")
print("="*80)
print("\n📊 فایل‌های ایجاد شده:")
print(f"   1. {summary_file}")
print(f"   2. {params_file}")
print("\n🔜 ادامه: نمودارهای بصری حجم نمونه...")