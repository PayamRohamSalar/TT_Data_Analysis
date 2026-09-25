# -*- coding: utf-8 -*-
"""
مرحله ۴ - بخش دوم: ایجاد جداول خلاصه و نمودارها
پروژه: تحلیل رفتار مشتریان بانک توسعه تعاون
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

import pickle
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
fm._rebuild()

if font_path.exists():
    font_manager.fontManager.addfont(str(font_path))
    plt.rcParams['font.family'] = 'Vazirmatn'
else:
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
# بارگذاری نتایج
# ==============================================================================

analysis_dir = FIGURES_DIR / 'analysis'
output_dir = FIGURES_DIR / 'sample_size'

print("="*80)
print("مرحله ۴ - بخش دوم: جداول و نمودارها")
print("="*80)

# بارگذاری نتایج بخش اول
with open(output_dir / 'sample_results.pkl', 'rb') as f:
    results = pickle.load(f)

# بارگذاری جمعیت
population_file = analysis_dir / 'table_population_estimates.xlsx'
df_population = pd.read_excel(population_file)

def extract_number(text):
    if isinstance(text, str):
        return int(text.split()[0].replace(',', ''))
    return int(text)

conservative_real = extract_number(df_population.loc[0, 'مشتریان حقیقی'])
conservative_legal = extract_number(df_population.loc[0, 'مشتریان حقوقی'])
optimistic_real = extract_number(df_population.loc[1, 'مشتریان حقیقی'])
optimistic_legal = extract_number(df_population.loc[1, 'مشتریان حقوقی'])

# ==============================================================================
# 1. جدول خلاصه حجم نمونه
# ==============================================================================

print("\n" + "="*80)
print("📊 جدول 1: خلاصه حجم نمونه")
print("="*80)

sample_summary_data = {
    'سناریو': ['محافظه‌کارانه', 'خوش‌بینانه'],
    'جمعیت حقیقی (پس از پالایش)': [
        f'{conservative_real:,}',
        f'{optimistic_real:,}'
    ],
    'نمونه حقیقی': [
        f'{results["conservative"]["real"]["n_final"]:,}',
        f'{results["optimistic"]["real"]["n_final"]:,}'
    ],
    'نسبت نمونه‌گیری حقیقی': [
        f'{results["conservative"]["real"]["sampling_ratio"]:.1f}%',
        f'{results["optimistic"]["real"]["sampling_ratio"]:.1f}%'
    ],
    'جمعیت حقوقی (پس از پالایش)': [
        f'{conservative_legal:,}',
        f'{optimistic_legal:,}'
    ],
    'نمونه حقوقی': [
        f'{results["conservative"]["legal"]:,}',
        f'{results["optimistic"]["legal"]:,}'
    ],
    'روش حقوقی': [
        results["conservative"]["legal_method"],
        results["optimistic"]["legal_method"]
    ]
}

df_sample_summary = pd.DataFrame(sample_summary_data)
print("\n")
print(df_sample_summary.to_string(index=False))

# ذخیره
summary_file = output_dir / 'table_sample_size_summary.xlsx'
df_sample_summary.to_excel(summary_file, index=False)
print(f"\n✓ جدول ذخیره شد: {summary_file}")

# ==============================================================================
# 2. جدول مراحل محاسبه
# ==============================================================================

print("\n" + "="*80)
print("📊 جدول 2: مراحل محاسبه (محافظه‌کارانه)")
print("="*80)

calculation_steps_data = {
    'مرحله': [
        '1. Cochran اولیه (n₀)',
        '2. FPC تصحیح شده',
        '3. حداقل ML (10×k×d)',
        '4. نسبت 15% جمعیت',
        '5. انتخاب حداکثر',
        '6. اعمال NR (1.10)'
    ],
    'فرمول/روش': [
        '(Z² × p × q) / e²',
        'n₀ / (1 + (n₀-1)/N)',
        '10 × 8 × 30',
        'N × 0.15',
        'max(مراحل 2،3،4)',
        'n × 1.10'
    ],
    'نتیجه (حقیقی)': [
        f'{results["conservative"]["real"]["n0_cochran"]:,}',
        f'{results["conservative"]["real"]["n_fpc"]:,}',
        f'{results["conservative"]["real"]["n_ml_minimum"]:,}',
        f'{results["conservative"]["real"]["n_15_percent"]:,}',
        f'{results["conservative"]["real"]["n_recommended"]:,}',
        f'{results["conservative"]["real"]["n_final"]:,}'
    ],
    'مرجع علمی': [
        'Cochran (1977)',
        'Cochran (1977)',
        'Ng (2019) - CS229',
        'Provost & Fawcett (2013)',
        'ترکیب رویکردها',
        'Groves et al. (2009)'
    ]
}

df_calculation_steps = pd.DataFrame(calculation_steps_data)
print("\n")
print(df_calculation_steps.to_string(index=False))

# ذخیره
steps_file = output_dir / 'table_calculation_steps.xlsx'
df_calculation_steps.to_excel(steps_file, index=False)
print(f"\n✓ جدول ذخیره شد: {steps_file}")

# ==============================================================================
# 3. جدول پارامترها و مراجع
# ==============================================================================

print("\n" + "="*80)
print("📊 جدول 3: پارامترها و مراجع علمی")
print("="*80)

parameters_data = {
    'پارامتر': [
        'سطح اطمینان',
        'Z-Score',
        'خطای مجاز (e)',
        'نسبت جمعیت (p)',
        'ضریب طراحی (DEFF)',
        'نرخ عدم پاسخ (NR)',
        'تعداد خوشه‌ها (k)',
        'تعداد ویژگی‌ها (d)',
        'نسبت ML پیشنهادی'
    ],
    'مقدار': [
        '95%',
        '1.96',
        '0.02 (2%)',
        '0.5',
        '1.0',
        '1.10 (10%)',
        '8',
        '30',
        '15% جمعیت'
    ],
    'مرجع علمی': [
        'استاندارد آماری',
        'جدول Z استاندارد',
        'Krejcie & Morgan (1970)',
        'Cochran (1977)',
        'Lohr (2019) - Stratified',
        'Groves et al. (2009)',
        'تخمین بر اساس پروژه',
        'تخمین بر اساس RFM',
        'Provost & Fawcett (2013)'
    ]
}

df_parameters = pd.DataFrame(parameters_data)
print("\n")
print(df_parameters.to_string(index=False))

# ذخیره
params_file = output_dir / 'table_parameters_references.xlsx'
df_parameters.to_excel(params_file, index=False)
print(f"\n✓ جدول ذخیره شد: {params_file}")

# ==============================================================================
# 4. نمودار 1: مقایسه جمعیت و نمونه
# ==============================================================================

print("\n" + "="*80)
print("📈 نمودار 1: مقایسه جمعیت و نمونه")
print("="*80)

fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(18, 14))

# محافظه‌کارانه - حقیقی
categories = [fix_persian_text('جمعیت\nپس از پالایش'), fix_persian_text('نمونه\nنهایی')]
values_cons_real = [conservative_real, results["conservative"]["real"]["n_final"]]
colors = ['#3498DB', '#27AE60']

bars = ax1.bar(categories, values_cons_real, color=colors, alpha=0.8, 
               edgecolor='black', linewidth=2, width=0.5)

for bar, value in zip(bars, values_cons_real):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height,
             format_number_with_separator(value, use_persian=True),
             ha='center', va='bottom', fontsize=12, fontweight='bold')

ratio = (results["conservative"]["real"]["n_final"] / conservative_real) * 100
ax1.text(0.5, conservative_real * 0.5,
         fix_persian_text(f'نسبت: {ratio:.1f}%'),
         ha='center', va='center', fontsize=14, fontweight='bold',
         bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))

ax1.set_title(fix_persian_text('محافظه‌کارانه - حقیقی'), fontsize=15, fontweight='bold', pad=15)
ax1.set_ylabel(fix_persian_text('تعداد'), fontsize=13, fontweight='bold')
ax1.grid(True, alpha=0.3, axis='y')
ax1.yaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: format_number_with_separator(int(x), use_persian=True)))

# خوش‌بینانه - حقیقی
values_opt_real = [optimistic_real, results["optimistic"]["real"]["n_final"]]

bars = ax2.bar(categories, values_opt_real, color=colors, alpha=0.8,
               edgecolor='black', linewidth=2, width=0.5)

for bar, value in zip(bars, values_opt_real):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height,
             format_number_with_separator(value, use_persian=True),
             ha='center', va='bottom', fontsize=12, fontweight='bold')

ratio = (results["optimistic"]["real"]["n_final"] / optimistic_real) * 100
ax2.text(0.5, optimistic_real * 0.5,
         fix_persian_text(f'نسبت: {ratio:.1f}%'),
         ha='center', va='center', fontsize=14, fontweight='bold',
         bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))

ax2.set_title(fix_persian_text('خوش‌بینانه - حقیقی'), fontsize=15, fontweight='bold', pad=15)
ax2.set_ylabel(fix_persian_text('تعداد'), fontsize=13, fontweight='bold')
ax2.grid(True, alpha=0.3, axis='y')
ax2.yaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: format_number_with_separator(int(x), use_persian=True)))

# محافظه‌کارانه - حقوقی
values_cons_legal = [conservative_legal, results["conservative"]["legal"]]

bars = ax3.bar(categories, values_cons_legal, color=['#E67E22', '#9B59B6'], alpha=0.8,
               edgecolor='black', linewidth=2, width=0.5)

for bar, value in zip(bars, values_cons_legal):
    height = bar.get_height()
    ax3.text(bar.get_x() + bar.get_width()/2., height,
             format_number_with_separator(value, use_persian=True),
             ha='center', va='bottom', fontsize=12, fontweight='bold')

ax3.text(0.5, conservative_legal * 0.5,
         fix_persian_text(f'روش: {results["conservative"]["legal_method"]}'),
         ha='center', va='center', fontsize=14, fontweight='bold',
         bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))

ax3.set_title(fix_persian_text('محافظه‌کارانه - حقوقی'), fontsize=15, fontweight='bold', pad=15)
ax3.set_ylabel(fix_persian_text('تعداد'), fontsize=13, fontweight='bold')
ax3.grid(True, alpha=0.3, axis='y')
ax3.yaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: format_number_with_separator(int(x), use_persian=True)))

# خوش‌بینانه - حقوقی
values_opt_legal = [optimistic_legal, results["optimistic"]["legal"]]

bars = ax4.bar(categories, values_opt_legal, color=['#E67E22', '#9B59B6'], alpha=0.8,
               edgecolor='black', linewidth=2, width=0.5)

for bar, value in zip(bars, values_opt_legal):
    height = bar.get_height()
    ax4.text(bar.get_x() + bar.get_width()/2., height,
             format_number_with_separator(value, use_persian=True),
             ha='center', va='bottom', fontsize=12, fontweight='bold')

ax4.text(0.5, optimistic_legal * 0.5,
         fix_persian_text(f'روش: {results["optimistic"]["legal_method"]}'),
         ha='center', va='center', fontsize=14, fontweight='bold',
         bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))

ax4.set_title(fix_persian_text('خوش‌بینانه - حقوقی'), fontsize=15, fontweight='bold', pad=15)
ax4.set_ylabel(fix_persian_text('تعداد'), fontsize=13, fontweight='bold')
ax4.grid(True, alpha=0.3, axis='y')
ax4.yaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: format_number_with_separator(int(x), use_persian=True)))

# استایل
for ax in [ax1, ax2, ax3, ax4]:
    ax.set_facecolor('#F8F9FA')
    for spine in ax.spines.values():
        spine.set_edgecolor('#CCCCCC')
        spine.set_linewidth(1.5)

fig.patch.set_facecolor('white')
plt.tight_layout()

output_path = output_dir / 'chart_population_vs_sample.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

print(f"✓ نمودار ذخیره شد: {output_path}")

# ==============================================================================
# 5. نمودار 2: نمودار جریان محاسبات
# ==============================================================================

print("\n" + "="*80)
print("📈 نمودار 2: فلوچارت مراحل محاسبه")
print("="*80)

fig, ax = plt.subplots(figsize=(16, 12))
ax.axis('off')

stages = [
    fix_persian_text(f'مرحله ۱: Cochran\nn₀ = {results["conservative"]["real"]["n0_cochran"]:,}'),
    fix_persian_text(f'مرحله ۲: FPC\nn = {results["conservative"]["real"]["n_fpc"]:,}'),
    fix_persian_text(f'مرحله ۳: حداقل ML\nn_ml = {results["conservative"]["real"]["n_ml_minimum"]:,}'),
    fix_persian_text(f'مرحله ۴: 15% جمعیت\nn_15% = {results["conservative"]["real"]["n_15_percent"]:,}'),
    fix_persian_text(f'مرحله ۵: حداکثر\nn = {results["conservative"]["real"]["n_recommended"]:,}'),
    fix_persian_text(f'مرحله ۶: NR (×1.10)\nn_final = {results["conservative"]["real"]["n_final"]:,}')
]

y_positions = [0.85, 0.70, 0.55, 0.40, 0.25, 0.10]
colors_flow = ['#E8F8F5', '#D1F2EB', '#A9DFBF', '#7DCEA0', '#52BE80', '#27AE60']

for i, (stage, y_pos, color) in enumerate(zip(stages, y_positions, colors_flow)):
    rect = plt.Rectangle((0.1, y_pos - 0.05), 0.8, 0.10,
                          facecolor=color, edgecolor='black', linewidth=2.5)
    ax.add_patch(rect)
    
    ax.text(0.5, y_pos, stage, ha='center', va='center',
            fontsize=13, fontweight='bold')
    
    if i < len(stages) - 1:
        ax.annotate('', xy=(0.5, y_positions[i+1] + 0.05),
                    xytext=(0.5, y_pos - 0.05),
                    arrowprops=dict(arrowstyle='->', lw=3, color='black'))

ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_title(fix_persian_text('فلوچارت محاسبه حجم نمونه (سناریو محافظه‌کارانه - حقیقی)'),
             fontsize=18, fontweight='bold', pad=20)

fig.patch.set_facecolor('white')
plt.tight_layout()

output_path = output_dir / 'chart_calculation_flowchart.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

print(f"✓ نمودار ذخیره شد: {output_path}")

# ==============================================================================
# خلاصه نهایی
# ==============================================================================

print("\n" + "="*80)
print("✅ مرحله ۴ کامل شد!")
print("="*80)
print("\n📊 فایل‌های ایجاد شده:")
print(f"   1. {summary_file.name}")
print(f"   2. {steps_file.name}")
print(f"   3. {params_file.name}")
print(f"   4. chart_population_vs_sample.png")
print(f"   5. chart_calculation_flowchart.png")

print(f"\n📁 مسیر: {output_dir}")

print("\n🎯 نتایج نهایی:")
print(f"\n   محافظه‌کارانه:")
print(f"      حقیقی: {results['conservative']['real']['n_final']:,} نمونه")
print(f"      حقوقی: {results['conservative']['legal']:,} ({results['conservative']['legal_method']})")

print(f"\n   خوش‌بینانه:")
print(f"      حقیقی: {results['optimistic']['real']['n_final']:,} نمونه")
print(f"      حقوقی: {results['optimistic']['legal']:,} ({results['optimistic']['legal_method']})")

print("\n📚 مراجع علمی کلیدی:")
print("   - Cochran (1977): Sampling Techniques")
print("   - Lohr (2019): Sampling: Design and Analysis")
print("   - Provost & Fawcett (2013): Data Science for Business")
print("   - Ng (2019): Stanford CS229 - Machine Learning")

print("\n✅ پروژه آماده برای مرحله بعد: تهیه گزارش نهایی")