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
output_dir = FIGURES_DIR / 'charts'
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
# Chart 2 (بهبود یافته): نمودار خطی روند Frequency در طول سال‌ها
# ==============================================================================

print("\n" + "="*80)
print("📈 نمودار ۲ (بهبود یافته): روند توزیع تکرار در سال‌های ۱۳۹۹-۱۴۰۴")
print("="*80)

# محاسبه درصد هر بازه در هر سال
years = sorted(df_frequency['سال'].unique())
transaction_ranges = ['صفر', 'یک تا سه', 'چهار تا شش', 'هفت تا دوازده', 
                      'سیزده تا بیست و چهار', 'بیست و پنج تا پنجاه', 'بیش از پنجاه']

# آماده‌سازی داده‌ها برای نمودار
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))

# رنگ‌های متمایز برای هر بازه
colors = ['#E74C3C', '#3498DB', '#2ECC71', '#F39C12', '#9B59B6', '#1ABC9C', '#34495E']

# === نمودار 1: مشتریان حقوقی ===
for i, trans_range in enumerate(transaction_ranges):
    df_range = df_frequency[df_frequency['تعداد تراکنش'] == trans_range]
    df_range = df_range.sort_values('سال')
    
    ax1.plot(df_range['سال'], df_range['تعداد مشتریان حقوقی'], 
             marker='o', linewidth=2.5, markersize=8, label=fix_persian_text(trans_range),
             color=colors[i], markeredgewidth=2, markeredgecolor='white')
    
    # افزودن مقادیر روی نقاط
    for x, y in zip(df_range['سال'], df_range['تعداد مشتریان حقوقی']):
        if y > 50000:  # فقط برای مقادیر بزرگ
            ax1.annotate(format_number_with_separator(int(y), use_persian=True),
                        xy=(x, y), xytext=(0, 10), textcoords='offset points',
                        ha='center', fontsize=7, fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

ax1.set_xlabel(fix_persian_text('سال'), fontsize=14, fontweight='bold')
ax1.set_ylabel(fix_persian_text('تعداد مشتریان'), fontsize=14, fontweight='bold')
ax1.set_title(fix_persian_text('روند توزیع تکرار تراکنش - مشتریان حقوقی (۱۳۹۹-۱۴۰۴)'), 
              fontsize=16, fontweight='bold', pad=20)
ax1.set_xticks(years)
ax1.set_xticklabels([convert_to_persian_number(y) for y in years], fontsize=12)
ax1.legend(loc='upper left', fontsize=10, ncol=2, framealpha=0.9)
ax1.grid(True, alpha=0.3, linestyle='--')
ax1.yaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: format_number_with_separator(int(x), use_persian=True)))

# === نمودار 2: مشتریان حقیقی ===
for i, trans_range in enumerate(transaction_ranges):
    df_range = df_frequency[df_frequency['تعداد تراکنش'] == trans_range]
    df_range = df_range.sort_values('سال')
    
    ax2.plot(df_range['سال'], df_range['تعداد مشتریان حقیقی'], 
             marker='o', linewidth=2.5, markersize=8, label=fix_persian_text(trans_range),
             color=colors[i], markeredgewidth=2, markeredgecolor='white')
    
    # افزودن مقادیر روی نقاط مهم
    for x, y in zip(df_range['سال'], df_range['تعداد مشتریان حقیقی']):
        if y > 1000000:  # فقط برای مقادیر بزرگ
            ax2.annotate(format_number_with_separator(int(y), use_persian=True),
                        xy=(x, y), xytext=(0, 10), textcoords='offset points',
                        ha='center', fontsize=7, fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

ax2.set_xlabel(fix_persian_text('سال'), fontsize=14, fontweight='bold')
ax2.set_ylabel(fix_persian_text('تعداد مشتریان'), fontsize=14, fontweight='bold')
ax2.set_title(fix_persian_text('روند توزیع تکرار تراکنش - مشتریان حقیقی (۱۳۹۹-۱۴۰۴)'), 
              fontsize=16, fontweight='bold', pad=20)
ax2.set_xticks(years)
ax2.set_xticklabels([convert_to_persian_number(y) for y in years], fontsize=12)
ax2.legend(loc='upper left', fontsize=10, ncol=2, framealpha=0.9)
ax2.grid(True, alpha=0.3, linestyle='--')
ax2.yaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: format_number_with_separator(int(x), use_persian=True)))

# استایل
for ax in [ax1, ax2]:
    ax.set_facecolor('#F8F9FA')
    for spine in ax.spines.values():
        spine.set_edgecolor('#CCCCCC')
        spine.set_linewidth(1.5)

fig.patch.set_facecolor('white')
plt.tight_layout()

output_path = output_dir / 'chart_2_frequency_trend.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

print(f"✓ نمودار ذخیره شد: {output_path}")


# ==============================================================================
# Chart 3 (بهبود یافته): Stacked Bar Chart - Monetary-Deposit در طول سال‌ها
# ==============================================================================

print("\n" + "="*80)
print("📈 نمودار ۳ (بهبود یافته): توزیع تجمعی ارزش سپرده در سال‌های ۱۳۹۹-۱۴۰۴")
print("="*80)

years = sorted(df_monetary_dep['سال'].unique())
deposit_ranges = df_monetary_dep['میانگین مانده سالانه'].unique()

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))

# رنگ‌های متمایز برای هر بازه
colors_deposit = ['#E8F8F5', '#A9DFBF', '#52BE80', '#27AE60', '#1E8449', '#145A32']

# === نمودار 1: مشتریان حقوقی - Stacked Bar ===
bottom_legal = np.zeros(len(years))

for i, deposit_range in enumerate(deposit_ranges):
    df_range = df_monetary_dep[df_monetary_dep['میانگین مانده سالانه'] == deposit_range]
    df_range = df_range.sort_values('سال')
    
    values = []
    for year in years:
        year_data = df_range[df_range['سال'] == year]
        if len(year_data) > 0:
            values.append(year_data['تعداد مشتریان حقوقی'].values[0])
        else:
            values.append(0)
    
    bars = ax1.bar(range(len(years)), values, bottom=bottom_legal, 
                   label=fix_persian_text(deposit_range), color=colors_deposit[i],
                   edgecolor='white', linewidth=1.5, width=0.6)
    
    # افزودن مقادیر روی ستون‌ها (فقط برای مقادیر بزرگ)
    for j, (bar, value) in enumerate(zip(bars, values)):
        if value > 5000:
            height = bar.get_height()
            y_pos = bottom_legal[j] + height/2
            ax1.text(bar.get_x() + bar.get_width()/2., y_pos,
                    format_number_with_separator(int(value), use_persian=True),
                    ha='center', va='center', fontsize=7, fontweight='bold',
                    color='white' if i > 2 else 'black')
    
    bottom_legal += np.array(values)

ax1.set_xlabel(fix_persian_text('سال'), fontsize=14, fontweight='bold')
ax1.set_ylabel(fix_persian_text('تعداد مشتریان'), fontsize=14, fontweight='bold')
ax1.set_title(fix_persian_text('توزیع تجمعی ارزش سپرده - مشتریان حقوقی'), 
              fontsize=15, fontweight='bold', pad=15)
ax1.set_xticks(range(len(years)))
ax1.set_xticklabels([convert_to_persian_number(y) for y in years], fontsize=12)
ax1.legend(loc='upper left', fontsize=9, framealpha=0.9)
ax1.grid(True, alpha=0.3, axis='y')
ax1.yaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: format_number_with_separator(int(x), use_persian=True)))

# === نمودار 2: مشتریان حقیقی - Stacked Bar ===
bottom_real = np.zeros(len(years))

for i, deposit_range in enumerate(deposit_ranges):
    df_range = df_monetary_dep[df_monetary_dep['میانگین مانده سالانه'] == deposit_range]
    df_range = df_range.sort_values('سال')
    
    values = []
    for year in years:
        year_data = df_range[df_range['سال'] == year]
        if len(year_data) > 0:
            values.append(year_data['تعداد مشتریان حقیقی'].values[0])
        else:
            values.append(0)
    
    bars = ax2.bar(range(len(years)), values, bottom=bottom_real, 
                   label=fix_persian_text(deposit_range), color=colors_deposit[i],
                   edgecolor='white', linewidth=1.5, width=0.6)
    
    # افزودن مقادیر روی ستون‌ها (فقط برای مقادیر بزرگ)
    for j, (bar, value) in enumerate(zip(bars, values)):
        if value > 200000:
            height = bar.get_height()
            y_pos = bottom_real[j] + height/2
            ax2.text(bar.get_x() + bar.get_width()/2., y_pos,
                    format_number_with_separator(int(value), use_persian=True),
                    ha='center', va='center', fontsize=7, fontweight='bold',
                    color='white' if i > 2 else 'black')
    
    bottom_real += np.array(values)

ax2.set_xlabel(fix_persian_text('سال'), fontsize=14, fontweight='bold')
ax2.set_ylabel(fix_persian_text('تعداد مشتریان'), fontsize=14, fontweight='bold')
ax2.set_title(fix_persian_text('توزیع تجمعی ارزش سپرده - مشتریان حقیقی'), 
              fontsize=15, fontweight='bold', pad=15)
ax2.set_xticks(range(len(years)))
ax2.set_xticklabels([convert_to_persian_number(y) for y in years], fontsize=12)
ax2.legend(loc='upper left', fontsize=9, framealpha=0.9)
ax2.grid(True, alpha=0.3, axis='y')
ax2.yaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: format_number_with_separator(int(x), use_persian=True)))

# استایل
for ax in [ax1, ax2]:
    ax.set_facecolor('#F8F9FA')
    for spine in ax.spines.values():
        spine.set_edgecolor('#CCCCCC')
        spine.set_linewidth(1.5)

fig.patch.set_facecolor('white')
plt.tight_layout()

output_path = output_dir / 'chart_3_monetary_deposit_stacked.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

print(f"✓ نمودار ذخیره شد: {output_path}")


# ==============================================================================
# Chart 4 (بهبود یافته): Histogram فراوانی - Monetary-Loan سال ۱۴۰۴
# ==============================================================================

print("\n" + "="*80)
print("📈 نمودار ۴ (بهبود یافته): هیستوگرام فراوانی ارزش تسهیلات - سال ۱۴۰۴")
print("="*80)

fig, axes = plt.subplots(2, 2, figsize=(18, 14))

# بازه‌های تسهیلات
loan_ranges = df_monetary_loan_1404['مانده تسهیلات'].unique()
loan_ranges_labels = [fix_persian_text(label) for label in loan_ranges]

# === نمودار 1: Histogram حقوقی ===
ax1 = axes[0, 0]
values_legal = df_monetary_loan_1404['تعداد مشتریان حقوقی '].values
x_pos = np.arange(len(loan_ranges))

bars1 = ax1.bar(x_pos, values_legal, color='#E67E22', alpha=0.8,
                edgecolor='black', linewidth=1.5, width=0.7)

# افزودن مقادیر و درصد
total_legal = values_legal.sum()
for i, (bar, value) in enumerate(zip(bars1, values_legal)):
    height = bar.get_height()
    percentage = (value / total_legal) * 100
    ax1.text(bar.get_x() + bar.get_width()/2., height,
             f'{format_number_with_separator(int(value), use_persian=True)}\n({percentage:.1f}٪)',
             ha='center', va='bottom', fontsize=9, fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

ax1.set_xlabel(fix_persian_text('بازه مانده تسهیلات'), fontsize=13, fontweight='bold')
ax1.set_ylabel(fix_persian_text('تعداد مشتریان'), fontsize=13, fontweight='bold')
ax1.set_title(fix_persian_text('هیستوگرام فراوانی - مشتریان حقوقی (۱۴۰۴)'), 
              fontsize=14, fontweight='bold', pad=15)
ax1.set_xticks(x_pos)
ax1.set_xticklabels(loan_ranges_labels, rotation=45, ha='right', fontsize=9)
ax1.grid(True, alpha=0.3, axis='y')
ax1.yaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: format_number_with_separator(int(x), use_persian=True)))

# === نمودار 2: Histogram حقیقی ===
ax2 = axes[0, 1]
values_real = df_monetary_loan_1404['تعداد مشتریان حقیقی'].values

bars2 = ax2.bar(x_pos, values_real, color='#8E44AD', alpha=0.8,
                edgecolor='black', linewidth=1.5, width=0.7)

# افزودن مقادیر و درصد
total_real = values_real.sum()
for i, (bar, value) in enumerate(zip(bars2, values_real)):
    height = bar.get_height()
    percentage = (value / total_real) * 100
    ax2.text(bar.get_x() + bar.get_width()/2., height,
             f'{format_number_with_separator(int(value), use_persian=True)}\n({percentage:.1f}٪)',
             ha='center', va='bottom', fontsize=9, fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

ax2.set_xlabel(fix_persian_text('بازه مانده تسهیلات'), fontsize=13, fontweight='bold')
ax2.set_ylabel(fix_persian_text('تعداد مشتریان'), fontsize=13, fontweight='bold')
ax2.set_title(fix_persian_text('هیستوگرام فراوانی - مشتریان حقیقی (۱۴۰۴)'), 
              fontsize=14, fontweight='bold', pad=15)
ax2.set_xticks(x_pos)
ax2.set_xticklabels(loan_ranges_labels, rotation=45, ha='right', fontsize=9)
ax2.grid(True, alpha=0.3, axis='y')
ax2.yaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: format_number_with_separator(int(x), use_persian=True)))

# === نمودار 3: نمودار دایره‌ای (Pie Chart) - حقوقی ===
ax3 = axes[1, 0]

# فقط بازه‌های با مقدار بالاتر از 1% را نمایش می‌دهیم
threshold = 0.01 * total_legal
filtered_values_legal = []
filtered_labels_legal = []
other_sum = 0

for i, (value, label) in enumerate(zip(values_legal, loan_ranges)):
    if value > threshold:
        filtered_values_legal.append(value)
        filtered_labels_legal.append(fix_persian_text(label))
    else:
        other_sum += value

if other_sum > 0:
    filtered_values_legal.append(other_sum)
    filtered_labels_legal.append(fix_persian_text('سایر'))

colors_pie = ['#E67E22', '#D35400', '#F39C12', '#F8B739', '#FDC830', '#FFA07A']
explode = [0.05 if i == 0 else 0 for i in range(len(filtered_values_legal))]

wedges, texts, autotexts = ax3.pie(filtered_values_legal, labels=filtered_labels_legal, 
                                     autopct='%1.1f%%', startangle=90, colors=colors_pie,
                                     explode=explode, textprops={'fontsize': 10, 'fontweight': 'bold'})

for autotext in autotexts:
    autotext.set_color('white')

ax3.set_title(fix_persian_text('توزیع درصدی - مشتریان حقوقی (۱۴۰۴)'), 
              fontsize=14, fontweight='bold', pad=15)

# === نمودار 4: نمودار دایره‌ای (Pie Chart) - حقیقی ===
ax4 = axes[1, 1]

# فقط بازه‌های با مقدار بالاتر از 1% را نمایش می‌دهیم
threshold_real = 0.01 * total_real
filtered_values_real = []
filtered_labels_real = []
other_sum_real = 0

for i, (value, label) in enumerate(zip(values_real, loan_ranges)):
    if value > threshold_real:
        filtered_values_real.append(value)
        filtered_labels_real.append(fix_persian_text(label))
    else:
        other_sum_real += value

if other_sum_real > 0:
    filtered_values_real.append(other_sum_real)
    filtered_labels_real.append(fix_persian_text('سایر'))

colors_pie2 = ['#8E44AD', '#9B59B6', '#A569BD', '#BB8FCE', '#D2B4DE', '#E8DAEF']
explode2 = [0.05 if i == 0 else 0 for i in range(len(filtered_values_real))]

wedges, texts, autotexts = ax4.pie(filtered_values_real, labels=filtered_labels_real, 
                                     autopct='%1.1f%%', startangle=90, colors=colors_pie2,
                                     explode=explode2, textprops={'fontsize': 10, 'fontweight': 'bold'})

for autotext in autotexts:
    autotext.set_color('white')

ax4.set_title(fix_persian_text('توزیع درصدی - مشتریان حقیقی (۱۴۰۴)'), 
              fontsize=14, fontweight='bold', pad=15)

# استایل
for ax in [ax1, ax2]:
    ax.set_facecolor('#F8F9FA')
    for spine in ax.spines.values():
        spine.set_edgecolor('#CCCCCC')
        spine.set_linewidth(1.5)

fig.patch.set_facecolor('white')
plt.tight_layout()

output_path = output_dir / 'chart_4_monetary_loan_histogram.png'
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