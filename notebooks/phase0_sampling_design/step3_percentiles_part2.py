# -*- coding: utf-8 -*-
"""
مرحله ۳ - بخش دوم: نمودارهای صدک Monetary و تخمین جمعیت هدف
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
matplotlib.use('Agg')  # اضافه کنید اگر ندارید

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
    # اضافه کردن فونت به سیستم
    fm.fontManager.addfont(str(font_path))
    plt.rcParams['font.family'] = 'Vazirmatn'
    print("✓ فونت Vazirmatn بارگذاری شد")
else:
    print("⚠ فونت Vazirmatn یافت نشد، از B Nazanin استفاده می‌شود")
    plt.rcParams['font.family'] = 'B Nazanin'

# تنظیمات اضافی
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.autolayout'] = True
plt.rcParams['font.size'] = 11

# بررسی فونت بارگذاری شده
print(f"فونت فعلی: {plt.rcParams['font.family']}")

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
# بارگذاری نتایج بخش اول (صدک‌ها)
# ==============================================================================

data_file = DATA_PROCESSED_DIR / 'RFM_Cleaned.xlsx'
output_dir = FIGURES_DIR / 'analysis'
percentiles_file = output_dir / 'table_percentiles_complete.xlsx'

print("="*80)
print("مرحله ۳ - بخش دوم: نمودارهای صدک و تخمین جمعیت")
print("="*80)

# بارگذاری جدول صدک‌ها
df_percentiles = pd.read_excel(percentiles_file)
print("\n✓ جدول صدک‌ها بارگذاری شد")

# بارگذاری داده‌های اصلی
df_monetary_dep = pd.read_excel(data_file, sheet_name='Monetary-Deposite')
df_monetary_loan = pd.read_excel(data_file, sheet_name='Monetary_Loan')
df_monetary_loan = df_monetary_loan.dropna()

df_monetary_dep_1404 = df_monetary_dep[df_monetary_dep['سال'] == 1404].copy()
df_monetary_loan_1404 = df_monetary_loan[df_monetary_loan['سال'] == 1404].copy()

# ==============================================================================
# 1. نمودار صدک‌ها - Monetary-Deposit
# ==============================================================================
print("\n" + "="*80)
print("📈 نمودار صدک‌های Monetary-Deposit")
print("="*80)

# استخراج مقادیر از جدول
deposit_percentiles = df_percentiles[df_percentiles['معیار'] == 'Monetary-Deposit (M.Rial)']

percentile_labels_mon = ['P10', 'P20', 'P50', 'P80', 'P90', 'P95']

# حقیقی
real_deposit = deposit_percentiles[deposit_percentiles['نوع مشتری'] == 'حقیقی'].iloc[0]
percentile_values_real_dep = [
    float(real_deposit['P10']),
    float(real_deposit['P20']),
    float(real_deposit['P50']),
    float(real_deposit['P80']),
    float(real_deposit['P90']),
    float(real_deposit['P95'])
]

# حقوقی
legal_deposit = deposit_percentiles[deposit_percentiles['نوع مشتری'] == 'حقوقی'].iloc[0]
percentile_values_legal_dep = [
    float(legal_deposit['P10']),
    float(legal_deposit['P20']),
    float(legal_deposit['P50']),
    float(legal_deposit['P80']),
    float(legal_deposit['P90']),
    float(legal_deposit['P95'])
]

# ترسیم نمودار
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))

colors_blue = ['#E8F5E9', '#A5D6A7', '#66BB6A', '#43A047', '#2E7D32', '#1B5E20']

# نمودار حقیقی
bars1 = ax1.bar(range(len(percentile_labels_mon)), percentile_values_real_dep, 
                color=colors_blue, edgecolor='black', linewidth=1.5, width=0.6)

ax1.axhline(y=percentile_values_real_dep[1], color='red', linestyle='--', 
            linewidth=2, label=fix_persian_text(f'آستانه P20 = {percentile_values_real_dep[1]:.0f}'))

for bar, value in zip(bars1, percentile_values_real_dep):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height,
             convert_to_persian_number(f'{int(value)}'),
             ha='center', va='bottom', fontsize=10, fontweight='bold')

ax1.set_xlabel(fix_persian_text('صدک'), fontsize=14, fontweight='bold')
ax1.set_ylabel(fix_persian_text('مانده سپرده (میلیون ریال)'), fontsize=14, fontweight='bold')
ax1.set_title(fix_persian_text('توزیع صدک‌های Monetary-Deposit - حقیقی'), 
              fontsize=15, fontweight='bold', pad=15)
ax1.set_xticks(range(len(percentile_labels_mon)))
ax1.set_xticklabels([convert_to_persian_number(p) for p in percentile_labels_mon], fontsize=12)
ax1.legend(fontsize=11, loc='upper left')
ax1.grid(True, alpha=0.3, axis='y')

# حذف مقیاس لگاریتمی و استفاده از مقیاس عادی
# ax1.set_yscale('log')  # این خط را حذف کنید

# تنظیم محور Y با اعداد فارسی
ax1.yaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: format_number_with_separator(int(x), use_persian=True)))

# نمودار حقوقی
bars2 = ax2.bar(range(len(percentile_labels_mon)), percentile_values_legal_dep, 
                color=colors_blue, edgecolor='black', linewidth=1.5, width=0.6)

ax2.axhline(y=percentile_values_legal_dep[1], color='red', linestyle='--', 
            linewidth=2, label=fix_persian_text(f'آستانه P20 = {percentile_values_legal_dep[1]:.0f}'))

for bar, value in zip(bars2, percentile_values_legal_dep):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height,
             convert_to_persian_number(f'{int(value)}'),
             ha='center', va='bottom', fontsize=10, fontweight='bold')

ax2.set_xlabel(fix_persian_text('صدک'), fontsize=14, fontweight='bold')
ax2.set_ylabel(fix_persian_text('مانده سپرده (میلیون ریال)'), fontsize=14, fontweight='bold')
ax2.set_title(fix_persian_text('توزیع صدک‌های Monetary-Deposit - حقوقی'), 
              fontsize=15, fontweight='bold', pad=15)
ax2.set_xticks(range(len(percentile_labels_mon)))
ax2.set_xticklabels([convert_to_persian_number(p) for p in percentile_labels_mon], fontsize=12)
ax2.legend(fontsize=11, loc='upper left')
ax2.grid(True, alpha=0.3, axis='y')

# حذف مقیاس لگاریتمی
# ax2.set_yscale('log')  # این خط را حذف کنید

# تنظیم محور Y با اعداد فارسی
ax2.yaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: format_number_with_separator(int(x), use_persian=True)))

for ax in [ax1, ax2]:
    ax.set_facecolor('#F8F9FA')
    for spine in ax.spines.values():
        spine.set_edgecolor('#CCCCCC')
        spine.set_linewidth(1.5)

fig.patch.set_facecolor('white')
plt.tight_layout()

output_path = output_dir / 'chart_percentiles_monetary_deposit.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

print(f"✓ نمودار ذخیره شد: {output_path}")

# ==============================================================================
# 2. نمودار مقایسه‌ای کلی آستانه‌ها
# ==============================================================================

print("\n" + "="*80)
print("📈 نمودار مقایسه‌ای آستانه‌های RFM")
print("="*80)

fig, ax = plt.subplots(figsize=(16, 10))

# داده‌های برای نمودار
criteria = [
    'Recency\n(6 ماه اخیر)', 
    'Frequency\n(≥P25)', 
    'Monetary-Deposit\n(≥P20)', 
    'Monetary-Loan\n(≥P20)', 
    'Tenure\n(≥12 ماه)'
]

# تبدیل به فارسی (تبدیل اعداد به فارسی)
criteria_persian = [fix_persian_text(convert_to_persian_number(c)) for c in criteria]

# درصدها
percentages_real = [43.2, 75.0, 80.0, 80.0, 88.2]
percentages_legal = [35.2, 75.0, 80.0, 80.0, 93.9]

x = np.arange(len(criteria_persian))
width = 0.35

bars1 = ax.bar(x - width/2, percentages_real, width, 
               label=fix_persian_text('مشتریان حقیقی'),
               color='#27AE60', alpha=0.8, edgecolor='black', linewidth=1.5)
bars2 = ax.bar(x + width/2, percentages_legal, width, 
               label=fix_persian_text('مشتریان حقوقی'),
               color='#3498DB', alpha=0.8, edgecolor='black', linewidth=1.5)

# افزودن مقادیر با تبدیل فارسی
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        percentage_str = f'{height:.1f}'
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{convert_to_persian_number(percentage_str)}٪',
                ha='center', va='bottom', fontsize=11, fontweight='bold')

ax.set_xlabel(fix_persian_text('معیار RFM'), fontsize=14, fontweight='bold')
ax.set_ylabel(fix_persian_text('درصد مشتریان واجد شرایط'), fontsize=14, fontweight='bold')
ax.set_title(fix_persian_text('مقایسه درصد مشتریان واجد شرایط بر اساس آستانه‌های RFM'), 
             fontsize=16, fontweight='bold', pad=20)
ax.set_xticks(x)
ax.set_xticklabels(criteria_persian, fontsize=12)
ax.legend(fontsize=13, loc='upper right')
ax.grid(True, alpha=0.3, axis='y')
ax.set_ylim([0, 100])

# خط مرجع 50%
ax.axhline(y=50, color='red', linestyle=':', linewidth=1.5, alpha=0.5)

# تبدیل اعداد محور Y به فارسی
ax.yaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: convert_to_persian_number(f'{int(x)}')))

ax.set_facecolor('#F8F9FA')
for spine in ax.spines.values():
    spine.set_edgecolor('#CCCCCC')
    spine.set_linewidth(1.5)

fig.patch.set_facecolor('white')
plt.tight_layout()

output_path = output_dir / 'chart_thresholds_comparison.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

print(f"✓ نمودار ذخیره شد: {output_path}")

# ==============================================================================
# 3. تخمین جمعیت هدف
# ==============================================================================

print("\n" + "="*80)
print("📊 تخمین جمعیت هدف (مشتریان فعال)")
print("="*80)

# جمعیت کل (از داده‌های Frequency 1404)
df_frequency_1404 = pd.read_excel(data_file, sheet_name='Frequency')
df_frequency_1404 = df_frequency_1404[df_frequency_1404['سال'] == 1404]

total_real = df_frequency_1404['تعداد مشتریان حقیقی'].sum()
total_legal = df_frequency_1404['تعداد مشتریان حقوقی'].sum()

print(f"\n📌 جمعیت کل (سال 1404):")
print(f"   حقیقی: {total_real:,} نفر")
print(f"   حقوقی: {total_legal:,} نفر")
print(f"   جمع: {total_real + total_legal:,} نفر")

# تخمین مشتریان فعال با اعمال فیلترهای RFM
# فرض: تقاطع معیارها (محافظه‌کارانه)

# Recency: 43.2% حقیقی، 35.2% حقوقی
# Frequency ≥ P25: 75%
# Monetary ≥ P20: 80%
# Tenure ≥ 12 ماه: 88.2% حقیقی، 93.9% حقوقی

# تخمین محافظه‌کارانه (ضرب احتمالات مستقل)
active_ratio_real = 0.432 * 0.75 * 0.80 * 0.882  # ≈ 22.8%
active_ratio_legal = 0.352 * 0.75 * 0.80 * 0.939  # ≈ 19.8%

# تخمین خوش‌بینانه (فرض همپوشانی بالا)
active_ratio_real_optimistic = 0.50  # 50%
active_ratio_legal_optimistic = 0.45  # 45%

# محاسبه تخمین‌ها
estimate_conservative_real = int(total_real * active_ratio_real)
estimate_conservative_legal = int(total_legal * active_ratio_legal)

estimate_optimistic_real = int(total_real * active_ratio_real_optimistic)
estimate_optimistic_legal = int(total_legal * active_ratio_legal_optimistic)

print(f"\n📊 تخمین مشتریان فعال (محافظه‌کارانه):")
print(f"   حقیقی: {estimate_conservative_real:,} نفر ({active_ratio_real*100:.1f}%)")
print(f"   حقوقی: {estimate_conservative_legal:,} نفر ({active_ratio_legal*100:.1f}%)")
print(f"   جمع: {estimate_conservative_real + estimate_conservative_legal:,} نفر")

print(f"\n📊 تخمین مشتریان فعال (خوش‌بینانه):")
print(f"   حقیقی: {estimate_optimistic_real:,} نفر ({active_ratio_real_optimistic*100:.1f}%)")
print(f"   حقوقی: {estimate_optimistic_legal:,} نفر ({active_ratio_legal_optimistic*100:.1f}%)")
print(f"   جمع: {estimate_optimistic_real + estimate_optimistic_legal:,} نفر")

# ==============================================================================
# 4. ایجاد جدول تخمین جمعیت
# ==============================================================================

population_estimates_data = {
    'سناریو': ['محافظه‌کارانه', 'خوش‌بینانه'],
    'مشتریان حقیقی': [
        f'{estimate_conservative_real:,} ({active_ratio_real*100:.1f}%)',
        f'{estimate_optimistic_real:,} ({active_ratio_real_optimistic*100:.1f}%)'
    ],
    'مشتریان حقوقی': [
        f'{estimate_conservative_legal:,} ({active_ratio_legal*100:.1f}%)',
        f'{estimate_optimistic_legal:,} ({active_ratio_legal_optimistic*100:.1f}%)'
    ],
    'جمع کل': [
        f'{estimate_conservative_real + estimate_conservative_legal:,}',
        f'{estimate_optimistic_real + estimate_optimistic_legal:,}'
    ]
}

df_population = pd.DataFrame(population_estimates_data)
print("\n📋 جدول تخمین جمعیت هدف:")
print(df_population.to_string(index=False))

# ذخیره
population_file = output_dir / 'table_population_estimates.xlsx'
df_population.to_excel(population_file, index=False)
print(f"\n✓ جدول ذخیره شد: {population_file}")

# ==============================================================================
# 5. نمودار قیفی (Funnel Chart) برای فرآیند پالایش
# ==============================================================================
print("\n" + "="*80)
print("📈 نمودار قیفی فرآیند پالایش")
print("="*80)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))

# داده‌های قیف - حقیقی
stages_real = [
    'جمعیت کل',
    'Recency ≤ 6 ماه',
    '+ Frequency ≥ P25',
    '+ Monetary ≥ P20',
    '+ Tenure ≥ 12 ماه'
]

# تبدیل برچسب‌ها به فارسی (تبدیل اعداد به فارسی)
stages_real_persian = [fix_persian_text(convert_to_persian_number(s)) for s in stages_real]

values_real = [
    total_real,
    int(total_real * 0.432),
    int(total_real * 0.432 * 0.75),
    int(total_real * 0.432 * 0.75 * 0.80),
    estimate_conservative_real
]

colors_funnel = ['#E8F8F5', '#A9DFBF', '#52BE80', '#27AE60', '#1E8449']

y_pos = np.arange(len(stages_real_persian))
bars1 = ax1.barh(y_pos, values_real, color=colors_funnel, 
                 edgecolor='black', linewidth=2, height=0.7)

for i, (bar, value) in enumerate(zip(bars1, values_real)):
    width = bar.get_width()
    percentage = (value / total_real) * 100
    # استفاده از توابع تبدیل فارسی
    value_text = format_number_with_separator(value, use_persian=True)
    percentage_text = convert_to_persian_number(f'{percentage:.1f}')
    
    ax1.text(width, bar.get_y() + bar.get_height()/2.,
             f' {value_text} ({percentage_text}٪)',
             ha='left', va='center', fontsize=11, fontweight='bold')

ax1.set_xlabel(fix_persian_text('تعداد مشتریان'), fontsize=14, fontweight='bold')
ax1.set_title(fix_persian_text('قیف پالایش - مشتریان حقیقی'), 
              fontsize=15, fontweight='bold', pad=15)
ax1.set_yticks(y_pos)
ax1.set_yticklabels(stages_real_persian, fontsize=11)
ax1.invert_yaxis()
ax1.grid(True, alpha=0.3, axis='x')
# اصلاح formatter محور X
ax1.xaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: format_number_with_separator(int(x), use_persian=True)))

# داده‌های قیف - حقوقی
stages_legal = stages_real
stages_legal_persian = stages_real_persian  # همان برچسب‌ها

values_legal = [
    total_legal,
    int(total_legal * 0.352),
    int(total_legal * 0.352 * 0.75),
    int(total_legal * 0.352 * 0.75 * 0.80),
    estimate_conservative_legal
]

bars2 = ax2.barh(y_pos, values_legal, color=colors_funnel, 
                 edgecolor='black', linewidth=2, height=0.7)

for i, (bar, value) in enumerate(zip(bars2, values_legal)):
    width = bar.get_width()
    percentage = (value / total_legal) * 100
    # استفاده از توابع تبدیل فارسی
    value_text = format_number_with_separator(value, use_persian=True)
    percentage_text = convert_to_persian_number(f'{percentage:.1f}')
    
    ax2.text(width, bar.get_y() + bar.get_height()/2.,
             f' {value_text} ({percentage_text}٪)',
             ha='left', va='center', fontsize=11, fontweight='bold')

ax2.set_xlabel(fix_persian_text('تعداد مشتریان'), fontsize=14, fontweight='bold')
ax2.set_title(fix_persian_text('قیف پالایش - مشتریان حقوقی'), 
              fontsize=15, fontweight='bold', pad=15)
ax2.set_yticks(y_pos)
ax2.set_yticklabels(stages_legal_persian, fontsize=11)
ax2.invert_yaxis()
ax2.grid(True, alpha=0.3, axis='x')
# اصلاح formatter محور X
ax2.xaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: format_number_with_separator(int(x), use_persian=True)))

for ax in [ax1, ax2]:
    ax.set_facecolor('#F8F9FA')
    for spine in ax.spines.values():
        spine.set_edgecolor('#CCCCCC')
        spine.set_linewidth(1.5)

fig.patch.set_facecolor('white')
plt.tight_layout()

output_path = output_dir / 'chart_filtering_funnel.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

print(f"✓ نمودار ذخیره شد: {output_path}")

# ==============================================================================
# خلاصه نهایی
# ==============================================================================

print("\n" + "="*80)
print("✅ مرحله ۳ کامل شد!")
print("="*80)
print("\n📊 فایل‌های ایجاد شده:")
print(f"   1. chart_percentiles_monetary_deposit.png")
print(f"   2. chart_thresholds_comparison.png")
print(f"   3. chart_filtering_funnel.png")
print(f"   4. table_population_estimates.xlsx")
print(f"\n📁 مسیر: {output_dir}")
print("\n🔜 آماده برای مرحله ۴: محاسبه حجم نمونه")