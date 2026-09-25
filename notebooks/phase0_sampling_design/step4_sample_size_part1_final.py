# -*- coding: utf-8 -*-
"""
مرحله ۴: محاسبه حجم نمونه (بر اساس متدولوژی علمی)
پروژه: تحلیل رفتار مشتریان بانک توسعه تعاون

استراتژی: ابتدا پالایش، سپس نمونه‌گیری
روش: Stratified Random Sampling با فرمول Cochran + ML Requirements
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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
#fm._rebuild()

if font_path.exists():
    font_manager.fontManager.addfont(str(font_path))
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
output_dir = FIGURES_DIR / 'sample_size'
output_dir.mkdir(exist_ok=True, parents=True)

print("="*80)
print("مرحله ۴: محاسبه حجم نمونه (روش‌شناسی علمی)")
print("="*80)
print(f"\n📁 مسیر خروجی: {output_dir}")
print("\n📚 روش: ابتدا پالایش، سپس نمونه‌گیری طبقه‌بندی شده")

# ==============================================================================
# 1. بارگذاری تخمین جمعیت هدف (پس از پالایش)
# ==============================================================================

print("\n" + "="*80)
print("📊 مرحله 1: جمعیت هدف (پس از پالایش RFM)")
print("="*80)

population_file = analysis_dir / 'table_population_estimates.xlsx'
df_population = pd.read_excel(population_file)

print("\n" + df_population.to_string(index=False))

# استخراج اعداد
def extract_number(text):
    if isinstance(text, str):
        return int(text.split()[0].replace(',', ''))
    return int(text)

# تخمین محافظه‌کارانه (پس از پالایش)
conservative_real = extract_number(df_population.loc[0, 'مشتریان حقیقی'])
conservative_legal = extract_number(df_population.loc[0, 'مشتریان حقوقی'])
conservative_total = conservative_real + conservative_legal

# تخمین خوش‌بینانه (پس از پالایش)
optimistic_real = extract_number(df_population.loc[1, 'مشتریان حقیقی'])
optimistic_legal = extract_number(df_population.loc[1, 'مشتریان حقوقی'])
optimistic_total = optimistic_real + optimistic_legal

print(f"\n📌 جمعیت فعال (پس از پالایش):")
print(f"\n   سناریو محافظه‌کارانه:")
print(f"      حقیقی: {conservative_real:,}")
print(f"      حقوقی: {conservative_legal:,}")
print(f"      جمع: {conservative_total:,}")

print(f"\n   سناریو خوش‌بینانه:")
print(f"      حقیقی: {optimistic_real:,}")
print(f"      حقوقی: {optimistic_legal:,}")
print(f"      جمع: {optimistic_total:,}")

# ==============================================================================
# 2. پارامترهای محاسبه حجم نمونه
# ==============================================================================

print("\n" + "="*80)
print("📊 مرحله 2: پارامترهای فرمول Cochran")
print("="*80)

# پارامترهای استاندارد
Z = 1.96          # سطح اطمینان 95%
e = 0.02          # خطای مجاز 2%
p = 0.5           # نسبت جمعیت (محافظه‌کارانه‌ترین)
q = 1 - p         # 0.5
NR = 1.10         # Non-Response Rate (10%)
DEFF = 1.0        # Design Effect (برای Stratified معمولاً 1.0)

# پارامترهای ML
k_clusters = 8    # تعداد خوشه‌های پیش‌بینی
d_features = 30   # تعداد ویژگی‌ها
ml_factor = 10    # ضریب استاندارد ML

print(f"\n📌 پارامترهای فرمول Cochran:")
print(f"   Z (سطح اطمینان 95%): {Z}")
print(f"   e (خطای مجاز): {e} ({e*100}%)")
print(f"   p (نسبت جمعیت): {p}")
print(f"   q (1-p): {q}")
print(f"   NR (نرخ عدم پاسخ): {NR} ({(NR-1)*100}%)")
print(f"   DEFF (ضریب طراحی): {DEFF}")

print(f"\n📌 پارامترهای ML:")
print(f"   تعداد خوشه‌ها (k): {k_clusters}")
print(f"   تعداد ویژگی‌ها (d): {d_features}")
print(f"   حداقل ML: {ml_factor} × k × d = {ml_factor * k_clusters * d_features:,}")

print(f"\n📚 مراجع علمی:")
print("""
   [1] Cochran (1977): "Sampling Techniques"
       → فرمول محاسبه حجم نمونه
   
   [2] Lohr (2019): "Sampling: Design and Analysis"
       → نمونه‌گیری طبقه‌بندی شده
   
   [3] Provost & Fawcett (2013): "Data Science for Business"
       → حجم نمونه برای ML: 10-30% جمعیت
   
   [4] Ng (2019): Stanford CS229
       → حداقل ML: n ≥ 10 × k × d
""")

# ==============================================================================
# 3. تابع محاسبه حجم نمونه (رویکرد ترکیبی)
# ==============================================================================

print("\n" + "="*80)
print("📊 مرحله 3: محاسبه حجم نمونه (رویکرد ترکیبی)")
print("="*80)

def calculate_sample_size_comprehensive(N, Z=1.96, e=0.02, p=0.5, 
                                       k=8, d=30, ml_factor=10,
                                       NR=1.10, DEFF=1.0):
    """
    محاسبه حجم نمونه با رویکرد ترکیبی Cochran + ML
    
    Parameters:
    -----------
    N : int
        جمعیت هدف (پس از پالایش)
    Z : float
        Z-score برای سطح اطمینان
    e : float
        خطای مجاز (margin of error)
    p : float
        نسبت جمعیت
    k : int
        تعداد خوشه‌ها
    d : int
        تعداد ویژگی‌ها
    ml_factor : int
        ضریب ML
    NR : float
        Non-Response Rate
    DEFF : float
        Design Effect
    
    Returns:
    --------
    dict : نتایج محاسبات در مراحل مختلف
    
    مراجع:
    -------
    - Cochran (1977): Sampling Techniques
    - Provost & Fawcett (2013): Data Science for Business
    - Ng (2019): Stanford CS229 - Machine Learning
    """
    
    q = 1 - p
    
    # مرحله 1: فرمول Cochran اولیه
    n0_cochran = (Z**2 * p * q) / (e**2)
    
    # مرحله 2: تصحیح برای جمعیت محدود (Finite Population Correction)
    n_fpc = n0_cochran / (1 + ((n0_cochran - 1) / N))
    
    # مرحله 3: حداقل برای ML
    n_ml_minimum = ml_factor * k * d
    
    # مرحله 4: 15% جمعیت (بر اساس تحقیقات ML)
    n_15_percent = 0.15 * N
    
    # مرحله 5: انتخاب حداکثر
    n_recommended = max(n_fpc, n_ml_minimum, n_15_percent)
    
    # مرحله 6: اعمال DEFF و NR
    n_final = n_recommended * DEFF * NR
    
    return {
        'n0_cochran': int(np.ceil(n0_cochran)),
        'n_fpc': int(np.ceil(n_fpc)),
        'n_ml_minimum': int(n_ml_minimum),
        'n_15_percent': int(np.ceil(n_15_percent)),
        'n_recommended': int(np.ceil(n_recommended)),
        'n_final': int(np.ceil(n_final)),
        'sampling_ratio': (n_final / N) * 100
    }

# ==============================================================================
# 4. محاسبه برای مشتریان حقیقی
# ==============================================================================

print("\n" + "="*80)
print("📊 گروه 1: مشتریان حقیقی (سپرده‌گذار)")
print("="*80)

# سناریو محافظه‌کارانه
print(f"\n📌 سناریو محافظه‌کارانه (N = {conservative_real:,}):")
sample_real_conservative = calculate_sample_size_comprehensive(
    conservative_real, Z, e, p, k_clusters, d_features, ml_factor, NR, DEFF
)

print(f"   مرحله 1 - Cochran اولیه: {sample_real_conservative['n0_cochran']:,}")
print(f"   مرحله 2 - FPC تصحیح شده: {sample_real_conservative['n_fpc']:,}")
print(f"   مرحله 3 - حداقل ML: {sample_real_conservative['n_ml_minimum']:,}")
print(f"   مرحله 4 - 15% جمعیت: {sample_real_conservative['n_15_percent']:,}")
print(f"   مرحله 5 - انتخاب حداکثر: {sample_real_conservative['n_recommended']:,}")
print(f"   مرحله 6 - نهایی (با NR): {sample_real_conservative['n_final']:,}")
print(f"   نسبت نمونه‌گیری: {sample_real_conservative['sampling_ratio']:.2f}%")

# سناریو خوش‌بینانه
print(f"\n📌 سناریو خوش‌بینانه (N = {optimistic_real:,}):")
sample_real_optimistic = calculate_sample_size_comprehensive(
    optimistic_real, Z, e, p, k_clusters, d_features, ml_factor, NR, DEFF
)

print(f"   مرحله 1 - Cochran اولیه: {sample_real_optimistic['n0_cochran']:,}")
print(f"   مرحله 2 - FPC تصحیح شده: {sample_real_optimistic['n_fpc']:,}")
print(f"   مرحله 3 - حداقل ML: {sample_real_optimistic['n_ml_minimum']:,}")
print(f"   مرحله 4 - 15% جمعیت: {sample_real_optimistic['n_15_percent']:,}")
print(f"   مرحله 5 - انتخاب حداکثر: {sample_real_optimistic['n_recommended']:,}")
print(f"   مرحله 6 - نهایی (با NR): {sample_real_optimistic['n_final']:,}")
print(f"   نسبت نمونه‌گیری: {sample_real_optimistic['sampling_ratio']:.2f}%")

# ==============================================================================
# 5. محاسبه برای مشتریان حقوقی (Census Decision)
# ==============================================================================

print("\n" + "="*80)
print("📊 گروه 2: مشتریان حقوقی (سپرده‌گذار)")
print("="*80)

# قاعده تصمیم‌گیری
CENSUS_THRESHOLD = 50000

print(f"\n📌 قاعده تصمیم‌گیری:")
print(f"   اگر N < {CENSUS_THRESHOLD:,} → Census (کل جمعیت)")
print(f"   اگر N ≥ {CENSUS_THRESHOLD:,} → Sampling")
print(f"\n   مرجع: Sudman (1976) - Applied Sampling")

# سناریو محافظه‌کارانه
print(f"\n📌 سناریو محافظه‌کارانه (N = {conservative_legal:,}):")
if conservative_legal < CENSUS_THRESHOLD:
    sample_legal_conservative = conservative_legal
    method_conservative = "Census"
    print(f"   ✓ تصمیم: استفاده از کل جمعیت (Census)")
    print(f"   حجم نمونه: {sample_legal_conservative:,} (100%)")
else:
    result = calculate_sample_size_comprehensive(
        conservative_legal, Z, e, p, k_clusters, d_features, ml_factor, NR, DEFF
    )
    sample_legal_conservative = result['n_final']
    method_conservative = "Sampling"
    print(f"   تصمیم: نمونه‌گیری")
    print(f"   حجم نمونه نهایی: {sample_legal_conservative:,}")

# سناریو خوش‌بینانه
print(f"\n📌 سناریو خوش‌بینانه (N = {optimistic_legal:,}):")
if optimistic_legal < CENSUS_THRESHOLD:
    sample_legal_optimistic = optimistic_legal
    method_optimistic = "Census"
    print(f"   ✓ تصمیم: استفاده از کل جمعیت (Census)")
    print(f"   حجم نمونه: {sample_legal_optimistic:,} (100%)")
else:
    result = calculate_sample_size_comprehensive(
        optimistic_legal, Z, e, p, k_clusters, d_features, ml_factor, NR, DEFF
    )
    sample_legal_optimistic = result['n_final']
    method_optimistic = "Sampling"
    print(f"   تصمیم: نمونه‌گیری")
    print(f"   حجم نمونه نهایی: {sample_legal_optimistic:,}")

# ==============================================================================
# 6. تخصیص نمونه به طبقات
# ==============================================================================

print("\n" + "="*80)
print("📊 مرحله 4: تخصیص نمونه به طبقات (Stratified Allocation)")
print("="*80)

# محاسبه نسبت‌ها
ratio_real_cons = conservative_real / conservative_total
ratio_legal_cons = conservative_legal / conservative_total

ratio_real_opt = optimistic_real / optimistic_total
ratio_legal_opt = optimistic_legal / optimistic_total

print(f"\n📌 نسبت‌های جمعیت:")
print(f"\n   محافظه‌کارانه:")
print(f"      حقیقی: {ratio_real_cons*100:.1f}%")
print(f"      حقوقی: {ratio_legal_cons*100:.1f}%")

print(f"\n   خوش‌بینانه:")
print(f"      حقیقی: {ratio_real_opt*100:.1f}%")
print(f"      حقوقی: {ratio_legal_opt*100:.1f}%")

print(f"\n💡 توضیح Proportional Allocation:")
print("""
   در این روش، نمونه از هر طبقه متناسب با اندازه آن طبقه
   در جمعیت کل انتخاب می‌شود.
   
   فرمول: n_h = n × (N_h / N)
   
   مرجع: Lohr (2019), Chapter 3 - Stratified Sampling
""")

# ==============================================================================
# ادامه در بخش بعدی...
# ==============================================================================

print("\n" + "="*80)
print("✅ مرحله ۴ - بخش اول کامل شد!")
print("="*80)
print("\n📊 نتایج کلیدی:")
print(f"\n   حقیقی (محافظه‌کارانه): {sample_real_conservative['n_final']:,}")
print(f"   حقیقی (خوش‌بینانه): {sample_real_optimistic['n_final']:,}")
print(f"\n   حقوقی (محافظه‌کارانه): {sample_legal_conservative:,} ({method_conservative})")
print(f"   حقوقی (خوش‌بینانه): {sample_legal_optimistic:,} ({method_optimistic})")
print("\n🔜 ادامه: ایجاد جداول و نمودارها...")

# ذخیره متغیرها برای بخش دوم
results = {
    'conservative': {
        'real': sample_real_conservative,
        'legal': sample_legal_conservative,
        'legal_method': method_conservative
    },
    'optimistic': {
        'real': sample_real_optimistic,
        'legal': sample_legal_optimistic,
        'legal_method': method_optimistic
    }
}

# ذخیره در فایل pickle برای بخش دوم
import pickle
with open(output_dir / 'sample_results.pkl', 'wb') as f:
    pickle.dump(results, f)

print(f"\n✓ نتایج ذخیره شد در: {output_dir / 'sample_results.pkl'}")