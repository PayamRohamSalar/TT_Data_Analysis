# -*- coding: utf-8 -*-
"""
مرحله ۳: محاسبه صدک‌ها و تعیین آستانه‌های پالایش
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

import matplotlib.pyplot as plt
import matplotlib as mpl

# ================= Font & Style (Copied from Step2) =================
mpl.rcParams['font.family'] = 'DejaVu Sans'
mpl.rcParams['font.size'] = 12
mpl.rcParams['axes.titlesize'] = 14
mpl.rcParams['axes.labelsize'] = 13
mpl.rcParams['xtick.labelsize'] = 11
mpl.rcParams['ytick.labelsize'] = 11
mpl.rcParams['legend.fontsize'] = 11

mpl.rcParams['axes.unicode_minus'] = False  # جلوگیری از مربع شدن علامت منفی
mpl.rcParams['figure.figsize'] = (10, 6)
mpl.rcParams['figure.dpi'] = 120
mpl.rcParams['savefig.dpi'] = 300
mpl.rcParams['axes.grid'] = True
mpl.rcParams['grid.alpha'] = 0.3
# ===================================================================

# کتابخانه‌های فارسی
import arabic_reshaper
from bidi.algorithm import get_display

# ==============================================================================
# Font Configuration
# ==============================================================================

font_path = FONTS_DIR / 'Vazirmatn-Regular.ttf'
if font_path.exists():
    font_manager.fontManager.addfont(str(font_path))
    plt.rcParams['font.family'] = 'Vazirmatn'
    print("✓ فونت Vazirmatn بارگذاری شد")
else:
    print("⚠ فونت Vazirmatn یافت نشد، از B Nazanin استفاده می‌شود")
    plt.rcParams['font.family'] = 'B Nazanin'

plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.autolayout'] = True

# تنظیمات اضافی برای حل مشکل نمایش
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 13
plt.rcParams['xtick.labelsize'] = 11
plt.rcParams['ytick.labelsize'] = 11

# ==============================================================================
# Helper Functions
# ==============================================================================

def fix_persian_text(text):
    """تبدیل متن فارسی به فرمت قابل نمایش"""
    if text is None or str(text).strip() == '':
        return ''
    try:
        reshaped_text = arabic_reshaper.reshape(str(text))
        bidi_text = get_display(reshaped_text)
        return bidi_text
    except Exception as e:
        return str(text)

def convert_to_persian_number(number):
    """تبدیل اعداد انگلیسی به فارسی"""
    english_digits = '0123456789'
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    translation_table = str.maketrans(english_digits, persian_digits)
    return str(number).translate(translation_table)

def format_number_with_separator(number, use_persian=True):
    """فرمت اعداد با جداکننده هزارگان"""
    formatted = f'{number:,.0f}' if isinstance(number, (int, float)) else str(number)
    if use_persian:
        return convert_to_persian_number(formatted)
    return formatted

# ==============================================================================
# Setup Paths
# ==============================================================================

data_file = DATA_PROCESSED_DIR / 'RFM_Cleaned.xlsx'
output_dir = FIGURES_DIR / 'analysis'
output_dir.mkdir(exist_ok=True, parents=True)

print("="*80)
print("مرحله ۳: محاسبه صدک‌ها و تعیین آستانه‌های پالایش")
print("="*80)
print(f"\n📁 مسیر داده: {data_file}")
print(f"📁 مسیر خروجی: {output_dir}")

# ==============================================================================
# Load Data
# ==============================================================================

print("\n" + "="*80)
print("📊 بارگذاری داده‌ها")
print("="*80)

df_recency = pd.read_excel(data_file, sheet_name='Recency')
df_frequency = pd.read_excel(data_file, sheet_name='Frequency')
df_monetary_dep = pd.read_excel(data_file, sheet_name='Monetary-Deposite')
df_tenure = pd.read_excel(data_file, sheet_name='Tenure')
df_monetary_loan = pd.read_excel(data_file, sheet_name='Monetary_Loan')
df_monetary_loan = df_monetary_loan.dropna()

# فیلتر سال 1404
df_frequency_1404 = df_frequency[df_frequency['سال'] == 1404].copy()
df_monetary_dep_1404 = df_monetary_dep[df_monetary_dep['سال'] == 1404].copy()
df_monetary_loan_1404 = df_monetary_loan[df_monetary_loan['سال'] == 1404].copy()

print("✓ داده‌ها بارگذاری شدند")

# ==============================================================================
# 1. محاسبه صدک‌ها برای Frequency
# ==============================================================================

print("\n" + "="*80)
print("📈 تحلیل ۱: محاسبه صدک‌ها - Frequency (تکرار)")
print("="*80)

# تعریف بازه‌های تراکنش به صورت عددی
frequency_ranges_map = {
    'صفر': 0,
    'یک تا سه': 2,
    'چهار تا شش': 5,
    'هفت تا دوازده': 9.5,
    'سیزده تا بیست و چهار': 18.5,
    'بیست و پنج تا پنجاه': 37.5,
    'بیش از پنجاه': 75
}

# محاسبه توزیع تجمعی برای حقیقی و حقوقی
def calculate_frequency_percentiles(df, customer_type):
    """محاسبه صدک‌ها بر اساس توزیع فراوانی"""
    
    # ایجاد آرایه توزیع
    distribution = []
    for _, row in df.iterrows():
        range_val = frequency_ranges_map.get(row['تعداد تراکنش'], 0)
        count = row[f'تعداد مشتریان {customer_type}']
        distribution.extend([range_val] * int(count))
    
    distribution = np.array(distribution)
    
    # محاسبه صدک‌ها
    percentiles = {
        'P10': np.percentile(distribution, 10),
        'P25': np.percentile(distribution, 25),
        'P50': np.percentile(distribution, 50),
        'P75': np.percentile(distribution, 75),
        'P90': np.percentile(distribution, 90),
        'P95': np.percentile(distribution, 95),
    }
    
    return percentiles, distribution

# محاسبه برای حقیقی
percentiles_real_freq, dist_real_freq = calculate_frequency_percentiles(df_frequency_1404, 'حقیقی')
print("\n📊 صدک‌های Frequency - مشتریان حقیقی (1404):")
for p, val in percentiles_real_freq.items():
    print(f"   {p}: {val:.2f} تراکنش")

# محاسبه برای حقوقی
percentiles_legal_freq, dist_legal_freq = calculate_frequency_percentiles(df_frequency_1404, 'حقوقی')
print("\n📊 صدک‌های Frequency - مشتریان حقوقی (1404):")
for p, val in percentiles_legal_freq.items():
    print(f"   {p}: {val:.2f} تراکنش")

# ==============================================================================
# 2. محاسبه صدک‌ها برای Monetary-Deposit
# ==============================================================================

print("\n" + "="*80)
print("📈 تحلیل ۲: محاسبه صدک‌ها - Monetary-Deposit (ارزش سپرده)")
print("="*80)

# تعریف بازه‌های مانده به صورت عددی (میلیون ریال)
monetary_dep_ranges_map = {
    'کمتر از ۱۰ میلیون ریال': 5,
    '۱۰ تا ۵۰ میلیون ریال': 30,
    '۵۰ تا ۲۰۰ میلیون ریال': 125,
    '۲۰۰ میلیون تا ۱ میلیارد ریال': 600,
    '۱ تا ۵ میلیارد ریال': 3000,
    'بیش از ۵ میلیارد ریال': 7500
}

def calculate_monetary_percentiles(df, customer_type, ranges_map):
    """محاسبه صدک‌ها برای ارزش پولی"""
    
    distribution = []
    for _, row in df.iterrows():
        range_val = ranges_map.get(row['میانگین مانده سالانه'], 0)
        count = row[f'تعداد مشتریان {customer_type}']
        distribution.extend([range_val] * int(count))
    
    distribution = np.array(distribution)
    
    percentiles = {
        'P10': np.percentile(distribution, 10),
        'P20': np.percentile(distribution, 20),
        'P50': np.percentile(distribution, 50),
        'P80': np.percentile(distribution, 80),
        'P90': np.percentile(distribution, 90),
        'P95': np.percentile(distribution, 95),
    }
    
    return percentiles, distribution

# محاسبه برای حقیقی
percentiles_real_dep, dist_real_dep = calculate_monetary_percentiles(
    df_monetary_dep_1404, 'حقیقی', monetary_dep_ranges_map)
print("\n📊 صدک‌های Monetary-Deposit - مشتریان حقیقی (1404):")
for p, val in percentiles_real_dep.items():
    print(f"   {p}: {val:.0f} میلیون ریال")

# محاسبه برای حقوقی
percentiles_legal_dep, dist_legal_dep = calculate_monetary_percentiles(
    df_monetary_dep_1404, 'حقوقی', monetary_dep_ranges_map)
print("\n📊 صدک‌های Monetary-Deposit - مشتریان حقوقی (1404):")
for p, val in percentiles_legal_dep.items():
    print(f"   {p}: {val:.0f} میلیون ریال")

# ==============================================================================
# 3. محاسبه صدک‌ها برای Monetary-Loan
# ==============================================================================
print("\n" + "="*80)
print("📈 تحلیل ۳: محاسبه صدک‌ها - Monetary-Loan (ارزش تسهیلات)")
print("="*80)

# تعریف بازه‌های تسهیلات (میلیون ریال)
monetary_loan_ranges_map = {
    'کمتر از ۵۰۰ میلیون ریال': 250,
    '۵۰۰ میلیون تا ۲ میلیارد ریال': 1250,
    '۲ تا ۱۰ میلیارد ریال': 6000,
    '۱۰ تا ۵۰ میلیارد ریال': 30000,
    '۵۰ تا ۲۰۰ میلیارد ریال': 125000,
    'بیش از ۲۰۰ میلیارد ریال': 300000
}

# تابع اصلاح شده برای Loan
def calculate_loan_percentiles(df, customer_type, ranges_map):
    """محاسبه صدک‌ها برای ارزش تسهیلات"""
    
    distribution = []
    for _, row in df.iterrows():
        # توجه: نام ستون 'مانده تسهیلات' است
        range_val = ranges_map.get(row['مانده تسهیلات'], 0)
        
        # توجه: برای حقوقی یک فاصله اضافی در انتهای نام ستون وجود دارد
        if customer_type == 'حقوقی':
            count = row['تعداد مشتریان حقوقی ']  # با فاصله در انتها
        else:
            count = row[f'تعداد مشتریان {customer_type}']
        
        distribution.extend([range_val] * int(count))
    
    distribution = np.array(distribution)
    
    percentiles = {
        'P10': np.percentile(distribution, 10),
        'P20': np.percentile(distribution, 20),
        'P50': np.percentile(distribution, 50),
        'P80': np.percentile(distribution, 80),
        'P90': np.percentile(distribution, 90),
        'P95': np.percentile(distribution, 95),
    }
    
    return percentiles, distribution

# محاسبه برای حقیقی
percentiles_real_loan, dist_real_loan = calculate_loan_percentiles(
    df_monetary_loan_1404, 'حقیقی', monetary_loan_ranges_map)
print("\n📊 صدک‌های Monetary-Loan - مشتریان حقیقی (1404):")
for p, val in percentiles_real_loan.items():
    print(f"   {p}: {val:.0f} میلیون ریال")

# محاسبه برای حقوقی
percentiles_legal_loan, dist_legal_loan = calculate_loan_percentiles(
    df_monetary_loan_1404, 'حقوقی', monetary_loan_ranges_map)
print("\n📊 صdک‌های Monetary-Loan - مشتریان حقوقی (1404):")
for p, val in percentiles_legal_loan.items():
    print(f"   {p}: {val:.0f} میلیون ریال")

# ==============================================================================
# 4. تحلیل Recency
# ==============================================================================

print("\n" + "="*80)
print("📈 تحلیل ۴: Recency (تازگی)")
print("="*80)

# محاسبه درصد مشتریان در 6 ماه اخیر
recent_ranges = [
    'از ابتدای فروردین 1404 تا پایان خرداد 1404',
    'از ابتدای تیر 1404 تا پایان مرداد 1404',
    'از ابتدای شهریور 1404 تا پایان آذر 1404'
]

recent_legal = df_recency[df_recency['بازه زمانی'].isin(recent_ranges)][
    'تعداد مشتریان حقوقی که آخرین تراکنش آنها در بازه زمانی مربوطه می باشد '].sum()
recent_real = df_recency[df_recency['بازه زمانی'].isin(recent_ranges)][
    'تعداد مشتریان حقیقی که آخرین تراکنش آنها در بازه زمانی مربوطه می باشد '].sum()

total_legal = df_recency['تعداد مشتریان حقوقی که آخرین تراکنش آنها در بازه زمانی مربوطه می باشد '].sum()
total_real = df_recency['تعداد مشتریان حقیقی که آخرین تراکنش آنها در بازه زمانی مربوطه می باشد '].sum()

print(f"\n📊 مشتریان فعال در 6 ماه اخیر (فروردین 1404 - آذر 1404):")
print(f"   حقوقی: {recent_legal:,} نفر ({recent_legal/total_legal*100:.1f}%)")
print(f"   حقیقی: {recent_real:,} نفر ({recent_real/total_real*100:.1f}%)")

# ==============================================================================
# 5. تحلیل Tenure
# ==============================================================================

print("\n" + "="*80)
print("📈 تحلیل ۵: Tenure (قدمت)")
print("="*80)

# مشتریان با قدمت بیش از 12 ماه
tenure_12m = df_tenure[~df_tenure['قدمت رابطه با بانک'].isin(['کمتر از 6 ماه', '6 تا 9 ماه', '9 تا 12 ماه'])]
tenure_12m_legal = tenure_12m['تعداد مشتریان حقوقی'].sum()
tenure_12m_real = tenure_12m['تعداد مشتریان حقیقی'].sum()

total_tenure_legal = df_tenure['تعداد مشتریان حقوقی'].sum()
total_tenure_real = df_tenure['تعداد مشتریان حقیقی'].sum()

print(f"\n📊 مشتریان با قدمت ≥ 12 ماه:")
print(f"   حقوقی: {tenure_12m_legal:,} نفر ({tenure_12m_legal/total_tenure_legal*100:.1f}%)")
print(f"   حقیقی: {tenure_12m_real:,} نفر ({tenure_12m_real/total_tenure_real*100:.1f}%)")

# ==============================================================================
# 6. ایجاد جدول خلاصه آستانه‌ها
# ==============================================================================

print("\n" + "="*80)
print("📊 جدول خلاصه آستانه‌های پالایش پیشنهادی")
print("="*80)

thresholds_data = {
    'معیار': ['Recency (تازگی)', 'Frequency (تکرار)', 'Monetary-Deposit (سپرده)', 
              'Monetary-Loan (تسهیلات)', 'Tenure (قدمت)'],
    'آستانه پیشنهادی': [
        '≤ 6 ماه',
        f'≥ P25 (حقیقی: {percentiles_real_freq["P25"]:.0f}، حقوقی: {percentiles_legal_freq["P25"]:.0f})',
        f'≥ P20 (حقیقی: {percentiles_real_dep["P20"]:.0f}M، حقوقی: {percentiles_legal_dep["P20"]:.0f}M)',
        f'≥ P20 (حقیقی: {percentiles_real_loan["P20"]:.0f}M، حقوقی: {percentiles_legal_loan["P20"]:.0f}M)',
        '≥ 12 ماه'
    ],
    'درصد واجد شرایط (حقیقی)': [
        f'{recent_real/total_real*100:.1f}%',
        '75%',
        '80%',
        '80%',
        f'{tenure_12m_real/total_tenure_real*100:.1f}%'
    ],
    'درصد واجد شرایط (حقوقی)': [
        f'{recent_legal/total_legal*100:.1f}%',
        '75%',
        '80%',
        '80%',
        f'{tenure_12m_legal/total_tenure_legal*100:.1f}%'
    ]
}

df_thresholds = pd.DataFrame(thresholds_data)
print("\n")
print(df_thresholds.to_string(index=False))

# ذخیره جدول
thresholds_file = output_dir / 'table_thresholds_summary.xlsx'
df_thresholds.to_excel(thresholds_file, index=False)
print(f"\n✓ جدول ذخیره شد: {thresholds_file}")

# ==============================================================================
# 7. ایجاد جدول کامل صدک‌ها
# ==============================================================================

print("\n" + "="*80)
print("📊 جدول کامل صدک‌ها")
print("="*80)

percentiles_full_data = {
    'معیار': [],
    'نوع مشتری': [],
    'P10': [],
    'P20': [],
    'P25': [],
    'P50': [],
    'P75': [],
    'P80': [],
    'P90': [],
    'P95': []
}

# Frequency
for customer_type, percentiles in [('حقیقی', percentiles_real_freq), ('حقوقی', percentiles_legal_freq)]:
    percentiles_full_data['معیار'].append('Frequency (تراکنش)')
    percentiles_full_data['نوع مشتری'].append(customer_type)
    percentiles_full_data['P10'].append(f"{percentiles.get('P10', '-'):.1f}")
    percentiles_full_data['P20'].append('-')
    percentiles_full_data['P25'].append(f"{percentiles.get('P25', '-'):.1f}")
    percentiles_full_data['P50'].append(f"{percentiles.get('P50', '-'):.1f}")
    percentiles_full_data['P75'].append(f"{percentiles.get('P75', '-'):.1f}")
    percentiles_full_data['P80'].append('-')
    percentiles_full_data['P90'].append(f"{percentiles.get('P90', '-'):.1f}")
    percentiles_full_data['P95'].append(f"{percentiles.get('P95', '-'):.1f}")

# Monetary-Deposit
for customer_type, percentiles in [('حقیقی', percentiles_real_dep), ('حقوقی', percentiles_legal_dep)]:
    percentiles_full_data['معیار'].append('Monetary-Deposit (M.Rial)')
    percentiles_full_data['نوع مشتری'].append(customer_type)
    percentiles_full_data['P10'].append(f"{percentiles.get('P10', 0):.0f}")
    percentiles_full_data['P20'].append(f"{percentiles.get('P20', 0):.0f}")
    percentiles_full_data['P25'].append('-')
    percentiles_full_data['P50'].append(f"{percentiles.get('P50', 0):.0f}")
    percentiles_full_data['P75'].append('-')
    percentiles_full_data['P80'].append(f"{percentiles.get('P80', 0):.0f}")
    percentiles_full_data['P90'].append(f"{percentiles.get('P90', 0):.0f}")
    percentiles_full_data['P95'].append(f"{percentiles.get('P95', 0):.0f}")

# Monetary-Loan
for customer_type, percentiles in [('حقیقی', percentiles_real_loan), ('حقوقی', percentiles_legal_loan)]:
    percentiles_full_data['معیار'].append('Monetary-Loan (M.Rial)')
    percentiles_full_data['نوع مشتری'].append(customer_type)
    percentiles_full_data['P10'].append(f"{percentiles.get('P10', 0):.0f}")
    percentiles_full_data['P20'].append(f"{percentiles.get('P20', 0):.0f}")
    percentiles_full_data['P25'].append('-')
    percentiles_full_data['P50'].append(f"{percentiles.get('P50', 0):.0f}")
    percentiles_full_data['P75'].append('-')
    percentiles_full_data['P80'].append(f"{percentiles.get('P80', 0):.0f}")
    percentiles_full_data['P90'].append(f"{percentiles.get('P90', 0):.0f}")
    percentiles_full_data['P95'].append(f"{percentiles.get('P95', 0):.0f}")

df_percentiles_full = pd.DataFrame(percentiles_full_data)
print("\n")
print(df_percentiles_full.to_string(index=False))

# ذخیره جدول
percentiles_file = output_dir / 'table_percentiles_complete.xlsx'
df_percentiles_full.to_excel(percentiles_file, index=False)
print(f"\n✓ جدول ذخیره شد: {percentiles_file}")

# ==============================================================================
# 8. نمودار بصری صدک‌ها - Frequency
# ==============================================================================
print("\n" + "="*80)
print("📈 ترسیم نمودار صدک‌ها - Frequency")
print("="*80)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))

# نمودار حقیقی
percentile_labels = ['P10', 'P25', 'P50', 'P75', 'P90', 'P95']
percentile_values_real = [percentiles_real_freq[p] for p in percentile_labels]

colors_gradient = ['#E8F8F5', '#A9DFBF', '#52BE80', '#27AE60', '#1E8449', '#145A32']
bars1 = ax1.bar(range(len(percentile_labels)), percentile_values_real, 
                color=colors_gradient, edgecolor='black', linewidth=1.5, width=0.6)

ax1.axhline(y=percentiles_real_freq['P25'], color='red', linestyle='--', 
            linewidth=2, label=fix_persian_text(f'آستانه پیشنهادی: P25 = {percentiles_real_freq["P25"]:.1f}'))

for bar, value in zip(bars1, percentile_values_real):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height,
             convert_to_persian_number(f'{value:.1f}'),  # استفاده از تابع تبدیل
             ha='center', va='bottom', fontsize=11, fontweight='bold')

ax1.set_xlabel(fix_persian_text('صدک'), fontsize=14, fontweight='bold')
ax1.set_ylabel(fix_persian_text('تعداد تراکنش سالانه'), fontsize=14, fontweight='bold')
ax1.set_title(fix_persian_text('توزیع صدک‌های Frequency - مشتریان حقیقی'), 
              fontsize=15, fontweight='bold', pad=15)
ax1.set_xticks(range(len(percentile_labels)))
# استفاده از تبدیل فارسی برای برچسب‌ها
ax1.set_xticklabels([convert_to_persian_number(p) for p in percentile_labels], fontsize=12)
ax1.legend(fontsize=11, loc='upper left')
ax1.grid(True, alpha=0.3, axis='y')

# تنظیم برچسب‌های محور Y با اعداد فارسی
ax1.yaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: convert_to_persian_number(f'{int(x)}')))

# نمودار حقوقی
percentile_values_legal = [percentiles_legal_freq[p] for p in percentile_labels]

bars2 = ax2.bar(range(len(percentile_labels)), percentile_values_legal, 
                color=colors_gradient, edgecolor='black', linewidth=1.5, width=0.6)

ax2.axhline(y=percentiles_legal_freq['P25'], color='red', linestyle='--', 
            linewidth=2, label=fix_persian_text(f'آستانه پیشنهادی: P25 = {percentiles_legal_freq["P25"]:.1f}'))

for bar, value in zip(bars2, percentile_values_legal):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height,
             convert_to_persian_number(f'{value:.1f}'),  # استفاده از تابع تبدیل
             ha='center', va='bottom', fontsize=11, fontweight='bold')

ax2.set_xlabel(fix_persian_text('صدک'), fontsize=14, fontweight='bold')
ax2.set_ylabel(fix_persian_text('تعداد تراکنش سالانه'), fontsize=14, fontweight='bold')
ax2.set_title(fix_persian_text('توزیع صدک‌های Frequency - مشتریان حقوقی'), 
              fontsize=15, fontweight='bold', pad=15)
ax2.set_xticks(range(len(percentile_labels)))
ax2.set_xticklabels([convert_to_persian_number(p) for p in percentile_labels], fontsize=12)
ax2.legend(fontsize=11, loc='upper left')
ax2.grid(True, alpha=0.3, axis='y')

# تنظیم برچسب‌های محور Y با اعداد فارسی
ax2.yaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: convert_to_persian_number(f'{int(x)}')))

# استایل
for ax in [ax1, ax2]:
    ax.set_facecolor('#F8F9FA')
    for spine in ax.spines.values():
        spine.set_edgecolor('#CCCCCC')
        spine.set_linewidth(1.5)

fig.patch.set_facecolor('white')
plt.tight_layout()

output_path = output_dir / 'chart_percentiles_frequency.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

print(f"✓ نمودار ذخیره شد: {output_path}")

# ==============================================================================
# ادامه در بخش بعدی...
# ==============================================================================

print("\n" + "="*80)
print("✅ مرحله ۳ - بخش اول کامل شد!")
print("="*80)
print("\n📊 فایل‌های ایجاد شده:")
print(f"   1. {thresholds_file}")
print(f"   2. {percentiles_file}")
print(f"   3. {output_path}")
print("\n🔜 ادامه: نمودارهای صدک برای Monetary...")