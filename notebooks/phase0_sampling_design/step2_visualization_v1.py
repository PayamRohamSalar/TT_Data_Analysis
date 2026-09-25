# -*- coding: utf-8 -*-
"""
مرحله ۲: تحلیل توزیع‌ها و ترسیم نمودارهای RFM
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

# تنظیم فونت فارسی - اگر Vazirmatn موجود باشد، استفاده می‌شود
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

# ==============================================================================
# Helper Functions for Persian Text
# ==============================================================================

def fix_persian_text(text):
    """تبدیل متن فارسی به فرمت قابل نمایش با تراز چپ"""
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
output_dir = FIGURES_DIR / 'charts' / 'Ver1'
output_dir.mkdir(exist_ok=True, parents=True)

print("="*80)
print("مرحله ۲: تحلیل توزیع‌ها و ترسیم نمودارهای RFM")
print("="*80)
print(f"\n📁 مسیر داده: {data_file}")
print(f"📁 مسیر خروجی نمودارها: {output_dir}")

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

# حذف ردیف‌های NaN از Monetary_Loan
df_monetary_loan = df_monetary_loan.dropna()

# فیلتر داده‌های سال 1404
df_frequency_1404 = df_frequency[df_frequency['سال'] == 1404].copy()
df_monetary_dep_1404 = df_monetary_dep[df_monetary_dep['سال'] == 1404].copy()
df_monetary_loan_1404 = df_monetary_loan[df_monetary_loan['سال'] == 1404].copy()

print(f"✓ Recency: {len(df_recency)} بازه")
print(f"✓ Frequency (1404): {len(df_frequency_1404)} بازه")
print(f"✓ Monetary-Deposite (1404): {len(df_monetary_dep_1404)} بازه")
print(f"✓ Monetary_Loan (1404): {len(df_monetary_loan_1404)} بازه")
print(f"✓ Tenure: {len(df_tenure)} بازه")

# ==============================================================================
# Chart 1: Recency Distribution
# ==============================================================================

print("\n" + "="*80)
print("📈 نمودار ۱: توزیع تازگی (Recency)")
print("="*80)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))

# نمودار حقوقی
x_pos = np.arange(len(df_recency) - 1)  # حذف ردیف آخر (کل)
labels = [fix_persian_text(label) for label in df_recency['بازه زمانی'].iloc[:-1]]
values_legal = df_recency['تعداد مشتریان حقوقی که آخرین تراکنش آنها در بازه زمانی مربوطه می باشد '].iloc[:-1].values

bars1 = ax1.barh(x_pos, values_legal, color='#3498DB', alpha=0.8,
                 edgecolor='black', linewidth=1.2)

ax1.set_xlabel(fix_persian_text('تعداد مشتریان'), fontsize=13, fontweight='bold')
ax1.set_ylabel(fix_persian_text('بازه زمانی'), fontsize=13, fontweight='bold')
ax1.set_title(fix_persian_text('توزیع تازگی - مشتریان حقوقی'), 
              fontsize=15, fontweight='bold', pad=15)
ax1.set_yticks(x_pos)
ax1.set_yticklabels(labels, fontsize=10)
ax1.grid(True, alpha=0.3, axis='x')
ax1.xaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: format_number_with_separator(int(x), use_persian=True)))

# افزودن مقادیر
for i, (bar, value) in enumerate(zip(bars1, values_legal)):
    ax1.text(value, bar.get_y() + bar.get_height()/2.,
             f' {format_number_with_separator(value, use_persian=True)}',
             ha='left', va='center', fontsize=9, fontweight='bold')

# نمودار حقیقی
values_real = df_recency['تعداد مشتریان حقیقی که آخرین تراکنش آنها در بازه زمانی مربوطه می باشد '].iloc[:-1].values

bars2 = ax2.barh(x_pos, values_real, color='#27AE60', alpha=0.8,
                 edgecolor='black', linewidth=1.2)

ax2.set_xlabel(fix_persian_text('تعداد مشتریان'), fontsize=13, fontweight='bold')
ax2.set_ylabel(fix_persian_text('بازه زمانی'), fontsize=13, fontweight='bold')
ax2.set_title(fix_persian_text('توزیع تازگی - مشتریان حقیقی'), 
              fontsize=15, fontweight='bold', pad=15)
ax2.set_yticks(x_pos)
ax2.set_yticklabels(labels, fontsize=10)
ax2.grid(True, alpha=0.3, axis='x')
ax2.xaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: format_number_with_separator(int(x), use_persian=True)))

# افزودن مقادیر
for i, (bar, value) in enumerate(zip(bars2, values_real)):
    ax2.text(value, bar.get_y() + bar.get_height()/2.,
             f' {format_number_with_separator(value, use_persian=True)}',
             ha='left', va='center', fontsize=9, fontweight='bold')

# استایل
for ax in [ax1, ax2]:
    ax.set_facecolor('#F8F9FA')
    for spine in ax.spines.values():
        spine.set_edgecolor('#CCCCCC')
        spine.set_linewidth(1.5)

fig.patch.set_facecolor('white')
plt.tight_layout()

output_path = output_dir / 'chart_1_recency_distribution.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

print(f"✓ نمودار ذخیره شد: {output_path}")

# ==============================================================================
# Chart 2: Frequency Distribution (1404)
# ==============================================================================

print("\n" + "="*80)
print("📈 نمودار ۲: توزیع تکرار (Frequency) - سال ۱۴۰۴")
print("="*80)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))

# نمودار حقوقی
x_pos = np.arange(len(df_frequency_1404))
labels = [fix_persian_text(label) for label in df_frequency_1404['تعداد تراکنش']]
values_legal = df_frequency_1404['تعداد مشتریان حقوقی'].values

bars1 = ax1.bar(x_pos, values_legal, color='#E74C3C', alpha=0.8,
                edgecolor='black', linewidth=1.2, width=0.7)

ax1.set_xlabel(fix_persian_text('بازه تعداد تراکنش'), fontsize=13, fontweight='bold')
ax1.set_ylabel(fix_persian_text('تعداد مشتریان'), fontsize=13, fontweight='bold')
ax1.set_title(fix_persian_text('توزیع تکرار - مشتریان حقوقی (۱۴۰۴)'), 
              fontsize=15, fontweight='bold', pad=15)
ax1.set_xticks(x_pos)
ax1.set_xticklabels(labels, rotation=45, ha='right', fontsize=10)
ax1.grid(True, alpha=0.3, axis='y')
ax1.yaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: format_number_with_separator(int(x), use_persian=True)))

# افزودن مقادیر
for bar in bars1:
    height = bar.get_height()
    if height > 0:
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                 format_number_with_separator(int(height), use_persian=True),
                 ha='center', va='bottom', fontsize=8, fontweight='bold', rotation=0)

# نمودار حقیقی
values_real = df_frequency_1404['تعداد مشتریان حقیقی'].values

bars2 = ax2.bar(x_pos, values_real, color='#9B59B6', alpha=0.8,
                edgecolor='black', linewidth=1.2, width=0.7)

ax2.set_xlabel(fix_persian_text('بازه تعداد تراکنش'), fontsize=13, fontweight='bold')
ax2.set_ylabel(fix_persian_text('تعداد مشتریان'), fontsize=13, fontweight='bold')
ax2.set_title(fix_persian_text('توزیع تکرار - مشتریان حقیقی (۱۴۰۴)'), 
              fontsize=15, fontweight='bold', pad=15)
ax2.set_xticks(x_pos)
ax2.set_xticklabels(labels, rotation=45, ha='right', fontsize=10)
ax2.grid(True, alpha=0.3, axis='y')
ax2.yaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: format_number_with_separator(int(x), use_persian=True)))

# افزودن مقادیر
for bar in bars2:
    height = bar.get_height()
    if height > 0:
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                 format_number_with_separator(int(height), use_persian=True),
                 ha='center', va='bottom', fontsize=8, fontweight='bold', rotation=0)

# استایل
for ax in [ax1, ax2]:
    ax.set_facecolor('#F8F9FA')
    for spine in ax.spines.values():
        spine.set_edgecolor('#CCCCCC')
        spine.set_linewidth(1.5)

fig.patch.set_facecolor('white')
plt.tight_layout()

output_path = output_dir / 'chart_2_frequency_distribution.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

print(f"✓ نمودار ذخیره شد: {output_path}")

# ==============================================================================
# Chart 3: Monetary-Deposit Distribution (1404)
# ==============================================================================

print("\n" + "="*80)
print("📈 نمودار ۳: توزیع ارزش سپرده (Monetary-Deposit) - سال ۱۴۰۴")
print("="*80)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))

# نمودار حقوقی
x_pos = np.arange(len(df_monetary_dep_1404))
labels = [fix_persian_text(label) for label in df_monetary_dep_1404['میانگین مانده سالانه']]
values_legal = df_monetary_dep_1404['تعداد مشتریان حقوقی'].values

bars1 = ax1.barh(x_pos, values_legal, color='#F39C12', alpha=0.8,
                 edgecolor='black', linewidth=1.2)

ax1.set_xlabel(fix_persian_text('تعداد مشتریان'), fontsize=13, fontweight='bold')
ax1.set_ylabel(fix_persian_text('بازه مانده سپرده'), fontsize=13, fontweight='bold')
ax1.set_title(fix_persian_text('توزیع ارزش سپرده - مشتریان حقوقی (۱۴۰۴)'), 
              fontsize=15, fontweight='bold', pad=15)
ax1.set_yticks(x_pos)
ax1.set_yticklabels(labels, fontsize=10)
ax1.grid(True, alpha=0.3, axis='x')
ax1.xaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: format_number_with_separator(int(x), use_persian=True)))

# افزودن مقادیر
for i, (bar, value) in enumerate(zip(bars1, values_legal)):
    ax1.text(value, bar.get_y() + bar.get_height()/2.,
             f' {format_number_with_separator(value, use_persian=True)}',
             ha='left', va='center', fontsize=9, fontweight='bold')

# نمودار حقیقی
values_real = df_monetary_dep_1404['تعداد مشتریان حقیقی'].values

bars2 = ax2.barh(x_pos, values_real, color='#16A085', alpha=0.8,
                 edgecolor='black', linewidth=1.2)

ax2.set_xlabel(fix_persian_text('تعداد مشتریان'), fontsize=13, fontweight='bold')
ax2.set_ylabel(fix_persian_text('بازه مانده سپرده'), fontsize=13, fontweight='bold')
ax2.set_title(fix_persian_text('توزیع ارزش سپرده - مشتریان حقیقی (۱۴۰۴)'), 
              fontsize=15, fontweight='bold', pad=15)
ax2.set_yticks(x_pos)
ax2.set_yticklabels(labels, fontsize=10)
ax2.grid(True, alpha=0.3, axis='x')
ax2.xaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: format_number_with_separator(int(x), use_persian=True)))

# افزودن مقادیر
for i, (bar, value) in enumerate(zip(bars2, values_real)):
    ax2.text(value, bar.get_y() + bar.get_height()/2.,
             f' {format_number_with_separator(value, use_persian=True)}',
             ha='left', va='center', fontsize=9, fontweight='bold')

# استایل
for ax in [ax1, ax2]:
    ax.set_facecolor('#F8F9FA')
    for spine in ax.spines.values():
        spine.set_edgecolor('#CCCCCC')
        spine.set_linewidth(1.5)

fig.patch.set_facecolor('white')
plt.tight_layout()

output_path = output_dir / 'chart_3_monetary_deposit_distribution.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

print(f"✓ نمودار ذخیره شد: {output_path}")

# ==============================================================================
# Chart 4: Monetary-Loan Distribution (1404)
# ==============================================================================

print("\n" + "="*80)
print("📈 نمودار ۴: توزیع ارزش تسهیلات (Monetary-Loan) - سال ۱۴۰۴")
print("="*80)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))

# نمودار حقوقی
x_pos = np.arange(len(df_monetary_loan_1404))
labels = [fix_persian_text(label) for label in df_monetary_loan_1404['مانده تسهیلات']]
values_legal = df_monetary_loan_1404['تعداد مشتریان حقوقی '].values

bars1 = ax1.barh(x_pos, values_legal, color='#D35400', alpha=0.8,
                 edgecolor='black', linewidth=1.2)

ax1.set_xlabel(fix_persian_text('تعداد مشتریان'), fontsize=13, fontweight='bold')
ax1.set_ylabel(fix_persian_text('بازه مانده تسهیلات'), fontsize=13, fontweight='bold')
ax1.set_title(fix_persian_text('توزیع ارزش تسهیلات - مشتریان حقوقی (۱۴۰۴)'), 
              fontsize=15, fontweight='bold', pad=15)
ax1.set_yticks(x_pos)
ax1.set_yticklabels(labels, fontsize=10)
ax1.grid(True, alpha=0.3, axis='x')
ax1.xaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: format_number_with_separator(int(x), use_persian=True)))

# افزودن مقادیر
for i, (bar, value) in enumerate(zip(bars1, values_legal)):
    ax1.text(value, bar.get_y() + bar.get_height()/2.,
             f' {format_number_with_separator(value, use_persian=True)}',
             ha='left', va='center', fontsize=9, fontweight='bold')

# نمودار حقیقی
values_real = df_monetary_loan_1404['تعداد مشتریان حقیقی'].values

bars2 = ax2.barh(x_pos, values_real, color='#8E44AD', alpha=0.8,
                 edgecolor='black', linewidth=1.2)

ax2.set_xlabel(fix_persian_text('تعداد مشتریان'), fontsize=13, fontweight='bold')
ax2.set_ylabel(fix_persian_text('بازه مانده تسهیلات'), fontsize=13, fontweight='bold')
ax2.set_title(fix_persian_text('توزیع ارزش تسهیلات - مشتریان حقیقی (۱۴۰۴)'), 
              fontsize=15, fontweight='bold', pad=15)
ax2.set_yticks(x_pos)
ax2.set_yticklabels(labels, fontsize=10)
ax2.grid(True, alpha=0.3, axis='x')
ax2.xaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: format_number_with_separator(int(x), use_persian=True)))

# افزودن مقادیر
for i, (bar, value) in enumerate(zip(bars2, values_real)):
    ax2.text(value, bar.get_y() + bar.get_height()/2.,
             f' {format_number_with_separator(value, use_persian=True)}',
             ha='left', va='center', fontsize=9, fontweight='bold')

# استایل
for ax in [ax1, ax2]:
    ax.set_facecolor('#F8F9FA')
    for spine in ax.spines.values():
        spine.set_edgecolor('#CCCCCC')
        spine.set_linewidth(1.5)

fig.patch.set_facecolor('white')
plt.tight_layout()

output_path = output_dir / 'chart_4_monetary_loan_distribution.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

print(f"✓ نمودار ذخیره شد: {output_path}")

# ==============================================================================
# Chart 5: Tenure Distribution
# ==============================================================================

print("\n" + "="*80)
print("📈 نمودار ۵: توزیع قدمت (Tenure)")
print("="*80)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))

# نمودار حقوقی
x_pos = np.arange(len(df_tenure))
labels = [fix_persian_text(label) for label in df_tenure['قدمت رابطه با بانک']]
values_legal = df_tenure['تعداد مشتریان حقوقی'].values

bars1 = ax1.bar(x_pos, values_legal, color='#2C3E50', alpha=0.8,
                edgecolor='black', linewidth=1.2, width=0.7)

ax1.set_xlabel(fix_persian_text('بازه قدمت'), fontsize=13, fontweight='bold')
ax1.set_ylabel(fix_persian_text('تعداد مشتریان'), fontsize=13, fontweight='bold')
ax1.set_title(fix_persian_text('توزیع قدمت - مشتریان حقوقی'), 
              fontsize=15, fontweight='bold', pad=15)
ax1.set_xticks(x_pos)
ax1.set_xticklabels(labels, rotation=45, ha='right', fontsize=10)
ax1.grid(True, alpha=0.3, axis='y')
ax1.yaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: format_number_with_separator(int(x), use_persian=True)))

# افزودن مقادیر
for bar in bars1:
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height,
             format_number_with_separator(int(height), use_persian=True),
             ha='center', va='bottom', fontsize=9, fontweight='bold', rotation=0)

# نمودار حقیقی
values_real = df_tenure['تعداد مشتریان حقیقی'].values

bars2 = ax2.bar(x_pos, values_real, color='#34495E', alpha=0.8,
                edgecolor='black', linewidth=1.2, width=0.7)

ax2.set_xlabel(fix_persian_text('بازه قدمت'), fontsize=13, fontweight='bold')
ax2.set_ylabel(fix_persian_text('تعداد مشتریان'), fontsize=13, fontweight='bold')
ax2.set_title(fix_persian_text('توزیع قدمت - مشتریان حقیقی'), 
              fontsize=15, fontweight='bold', pad=15)
ax2.set_xticks(x_pos)
ax2.set_xticklabels(labels, rotation=45, ha='right', fontsize=10)
ax2.grid(True, alpha=0.3, axis='y')
ax2.yaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: format_number_with_separator(int(x), use_persian=True)))

# افزودن مقادیر
for bar in bars2:
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height,
             format_number_with_separator(int(height), use_persian=True),
             ha='center', va='bottom', fontsize=9, fontweight='bold', rotation=0)

# استایل
for ax in [ax1, ax2]:
    ax.set_facecolor('#F8F9FA')
    for spine in ax.spines.values():
        spine.set_edgecolor('#CCCCCC')
        spine.set_linewidth(1.5)

fig.patch.set_facecolor('white')
plt.tight_layout()

output_path = output_dir / 'chart_5_tenure_distribution.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

print(f"✓ نمودار ذخیره شد: {output_path}")

# ==============================================================================
# Summary
# ==============================================================================

print("\n" + "="*80)
print("✅ مرحله ۲ با موفقیت کامل شد!")
print("="*80)
print("\n📊 نمودارهای ایجاد شده:")
print("   1. chart_1_recency_distribution.png")
print("   2. chart_2_frequency_distribution.png")
print("   3. chart_3_monetary_deposit_distribution.png")
print("   4. chart_4_monetary_loan_distribution.png")
print("   5. chart_5_tenure_distribution.png")
print(f"\n📁 مسیر ذخیره: {output_dir}")
print("\n🔜 آماده برای مرحله ۳: محاسبه صدک‌ها و تعیین آستانه‌ها")