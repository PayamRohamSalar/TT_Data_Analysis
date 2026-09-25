# -*- coding: utf-8 -*-
"""
مرحله ۴ - بخش دوم: نمودارهای بصری حجم نمونه
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
# بارگذاری داده‌ها
# ==============================================================================

output_dir = FIGURES_DIR / 'sample_size' / 'v1'

print("="*80)
print("مرحله ۴ - بخش دوم: نمودارهای بصری")
print("="*80)

# بارگذاری جدول خلاصه
summary_file = output_dir / 'table_sample_size_summary.xlsx'
df_summary = pd.read_excel(summary_file)

# استخراج اعداد
def extract_number(text):
    if isinstance(text, str):
        return int(text.replace(',', ''))
    return int(text)

# سناریو محافظه‌کارانه
conservative_N = extract_number(df_summary.loc[0, 'جمعیت هدف (N)'])
conservative_n = extract_number(df_summary.loc[0, 'حجم نمونه نهایی'])
conservative_real = extract_number(df_summary.loc[0, 'نمونه حقیقی'])
conservative_legal = extract_number(df_summary.loc[0, 'نمونه حقوقی'])

# سناریو خوش‌بینانه
optimistic_N = extract_number(df_summary.loc[1, 'جمعیت هدف (N)'])
optimistic_n = extract_number(df_summary.loc[1, 'حجم نمونه نهایی'])
optimistic_real = extract_number(df_summary.loc[1, 'نمونه حقیقی'])
optimistic_legal = extract_number(df_summary.loc[1, 'نمونه حقوقی'])

# ==============================================================================
# نمودار 1: مقایسه جمعیت و نمونه
# ==============================================================================

print("\n📈 نمودار ۱: مقایسه جمعیت هدف و حجم نمونه")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))

# محافظه‌کارانه
categories_cons = [fix_persian_text('جمعیت هدف'), fix_persian_text('حجم نمونه')]
values_cons = [conservative_N, conservative_n]
colors_cons = ['#3498DB', '#27AE60']

bars1 = ax1.bar(categories_cons, values_cons, color=colors_cons, 
                alpha=0.8, edgecolor='black', linewidth=2, width=0.6)

for bar, value in zip(bars1, values_cons):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height,
             format_number_with_separator(value, use_persian=True),
             ha='center', va='bottom', fontsize=13, fontweight='bold')

# محاسبه نسبت نمونه‌گیری
sampling_ratio_cons = (conservative_n / conservative_N) * 100
ax1.text(0.5, conservative_N * 0.5, 
         fix_persian_text(f'نسبت نمونه‌گیری:\n{sampling_ratio_cons:.2f}%'),
         ha='center', va='center', fontsize=14, fontweight='bold',
         bbox=dict(boxstyle='round,pad=0.8', facecolor='yellow', alpha=0.7))

ax1.set_ylabel(fix_persian_text('تعداد'), fontsize=14, fontweight='bold')
ax1.set_title(fix_persian_text('سناریو محافظه‌کارانه'), 
              fontsize=16, fontweight='bold', pad=15)
ax1.grid(True, alpha=0.3, axis='y')
ax1.yaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: format_number_with_separator(int(x), use_persian=True)))

# خوش‌بینانه
categories_opt = categories_cons
values_opt = [optimistic_N, optimistic_n]

bars2 = ax2.bar(categories_opt, values_opt, color=colors_cons, 
                alpha=0.8, edgecolor='black', linewidth=2, width=0.6)

for bar, value in zip(bars2, values_opt):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height,
             format_number_with_separator(value, use_persian=True),
             ha='center', va='bottom', fontsize=13, fontweight='bold')

sampling_ratio_opt = (optimistic_n / optimistic_N) * 100
ax2.text(0.5, optimistic_N * 0.5, 
         fix_persian_text(f'نسبت نمونه‌گیری:\n{sampling_ratio_opt:.2f}%'),
         ha='center', va='center', fontsize=14, fontweight='bold',
         bbox=dict(boxstyle='round,pad=0.8', facecolor='yellow', alpha=0.7))

ax2.set_ylabel(fix_persian_text('تعداد'), fontsize=14, fontweight='bold')
ax2.set_title(fix_persian_text('سناریو خوش‌بینانه'), 
              fontsize=16, fontweight='bold', pad=15)
ax2.grid(True, alpha=0.3, axis='y')
ax2.yaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: format_number_with_separator(int(x), use_persian=True)))

for ax in [ax1, ax2]:
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
# نمودار 2: توزیع نمونه بین حقیقی و حقوقی
# ==============================================================================

print("\n📈 نمودار ۲: توزیع نمونه بین مشتریان حقیقی و حقوقی")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))

# نمودار دایره‌ای محافظه‌کارانه
labels_cons = [fix_persian_text('حقیقی'), fix_persian_text('حقوقی')]
sizes_cons = [conservative_real, conservative_legal]
colors_pie = ['#27AE60', '#3498DB']
explode = (0.05, 0)

wedges, texts, autotexts = ax1.pie(sizes_cons, labels=labels_cons, autopct='%1.1f%%',
                                     startangle=90, colors=colors_pie, explode=explode,
                                     textprops={'fontsize': 13, 'fontweight': 'bold'})

for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontsize(14)

# افزودن اعداد به legend
legend_labels = [
    f'{fix_persian_text("حقیقی")}: {format_number_with_separator(conservative_real, use_persian=True)}',
    f'{fix_persian_text("حقوقی")}: {format_number_with_separator(conservative_legal, use_persian=True)}'
]
ax1.legend(legend_labels, loc='upper left', fontsize=11, framealpha=0.9)

ax1.set_title(fix_persian_text('سناریو محافظه‌کارانه'), 
              fontsize=16, fontweight='bold', pad=15)

# نمودار دایره‌ای خوش‌بینانه
labels_opt = labels_cons
sizes_opt = [optimistic_real, optimistic_legal]

wedges, texts, autotexts = ax2.pie(sizes_opt, labels=labels_opt, autopct='%1.1f%%',
                                     startangle=90, colors=colors_pie, explode=explode,
                                     textprops={'fontsize': 13, 'fontweight': 'bold'})

for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontsize(14)

legend_labels_opt = [
    f'{fix_persian_text("حقیقی")}: {format_number_with_separator(optimistic_real, use_persian=True)}',
    f'{fix_persian_text("حقوقی")}: {format_number_with_separator(optimistic_legal, use_persian=True)}'
]
ax2.legend(legend_labels_opt, loc='upper left', fontsize=11, framealpha=0.9)

ax2.set_title(fix_persian_text('سناریو خوش‌بینانه'), 
              fontsize=16, fontweight='bold', pad=15)

fig.patch.set_facecolor('white')
plt.tight_layout()

output_path = output_dir / 'chart_sample_distribution.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

print(f"✓ نمودار ذخیره شد: {output_path}")

# ==============================================================================
# نمودار 3: مقایسه دو سناریو
# ==============================================================================

print("\n📈 نمودار ۳: مقایسه دو سناریو")

fig, ax = plt.subplots(figsize=(16, 9))

categories = [fix_persian_text('جمعیت هدف'), fix_persian_text('حجم نمونه'), 
              fix_persian_text('نمونه حقیقی'), fix_persian_text('نمونه حقوقی')]
conservative_values = [conservative_N, conservative_n, conservative_real, conservative_legal]
optimistic_values = [optimistic_N, optimistic_n, optimistic_real, optimistic_legal]

x = np.arange(len(categories))
width = 0.35

bars1 = ax.bar(x - width/2, conservative_values, width, 
               label=fix_persian_text('محافظه‌کارانه'),
               color='#E67E22', alpha=0.8, edgecolor='black', linewidth=1.5)
bars2 = ax.bar(x + width/2, optimistic_values, width, 
               label=fix_persian_text('خوش‌بینانه'),
               color='#9B59B6', alpha=0.8, edgecolor='black', linewidth=1.5)

# افزودن مقادیر
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                format_number_with_separator(int(height), use_persian=True),
                ha='center', va='bottom', fontsize=10, fontweight='bold', rotation=0)

ax.set_ylabel(fix_persian_text('تعداد'), fontsize=14, fontweight='bold')
ax.set_title(fix_persian_text('مقایسه سناریوهای محافظه‌کارانه و خوش‌بینانه'), 
             fontsize=16, fontweight='bold', pad=20)
ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=12)
ax.legend(fontsize=13, loc='upper right')
ax.grid(True, alpha=0.3, axis='y')

ax.yaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: format_number_with_separator(int(x), use_persian=True)))

ax.set_facecolor('#F8F9FA')
for spine in ax.spines.values():
    spine.set_edgecolor('#CCCCCC')
    spine.set_linewidth(1.5)

fig.patch.set_facecolor('white')
plt.tight_layout()

output_path = output_dir / 'chart_scenarios_comparison.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

print(f"✓ نمودار ذخیره شد: {output_path}")

# ==============================================================================
# نمودار 4: فرآیند محاسبه (Flow Chart)
# ==============================================================================

print("\n📈 نمودار ۴: مراحل محاسبه حجم نمونه")

fig, ax = plt.subplots(figsize=(16, 10))
ax.axis('off')

# داده‌های محافظه‌کارانه برای مثال
n0_cons = extract_number(df_summary.loc[0, 'حجم نمونه اولیه (n₀)'])
n_adj_cons = extract_number(df_summary.loc[0, 'حجم نمونه تصحیح شده'])

stages = [
    fix_persian_text(f'مرحله ۱: حجم نمونه اولیه\nn₀ = {format_number_with_separator(n0_cons, use_persian=True)}'),
    fix_persian_text(f'مرحله ۲: تصحیح جمعیت محدود\nn = {format_number_with_separator(n_adj_cons, use_persian=True)}'),
    fix_persian_text(f'مرحله ۳: اعمال DEFF و NR\nn_final = {format_number_with_separator(conservative_n, use_persian=True)}'),
    fix_persian_text(f'مرحله ۴: تخصیص به طبقات\nحقیقی: {format_number_with_separator(conservative_real, use_persian=True)}\nحقوقی: {format_number_with_separator(conservative_legal, use_persian=True)}')
]

y_positions = [0.75, 0.5, 0.25, 0.0]
colors_flow = ['#E8F8F5', '#A9DFBF', '#52BE80', '#27AE60']

for i, (stage, y_pos, color) in enumerate(zip(stages, y_positions, colors_flow)):
    # رسم مستطیل
    rect = plt.Rectangle((0.15, y_pos - 0.08), 0.7, 0.15, 
                          facecolor=color, edgecolor='black', linewidth=2)
    ax.add_patch(rect)
    
    # افزودن متن
    ax.text(0.5, y_pos, stage, ha='center', va='center', 
            fontsize=13, fontweight='bold')
    
    # افزودن فلش
    if i < len(stages) - 1:
        ax.annotate('', xy=(0.5, y_positions[i+1] + 0.07), 
                    xytext=(0.5, y_pos - 0.08),
                    arrowprops=dict(arrowstyle='->', lw=3, color='black'))

ax.set_xlim(0, 1)
ax.set_ylim(-0.15, 0.95)
ax.set_title(fix_persian_text('مراحل محاسبه حجم نمونه - سناریو محافظه‌کارانه'), 
             fontsize=18, fontweight='bold', pad=20)

fig.patch.set_facecolor('white')
plt.tight_layout()

output_path = output_dir / 'chart_calculation_process.png'
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
print(f"   1. chart_population_vs_sample.png")
print(f"   2. chart_sample_distribution.png")
print(f"   3. chart_scenarios_comparison.png")
print(f"   4. chart_calculation_process.png")
print(f"\n📁 مسیر: {output_dir}")
print("\n🎯 نتیجه نهایی:")
print(f"   سناریو محافظه‌کارانه: {conservative_n:,} نمونه")
print(f"   سناریو خوش‌بینانه: {optimistic_n:,} نمونه")
print("\n🔜 آماده برای مرحله ۵: تهیه گزارش نهایی")