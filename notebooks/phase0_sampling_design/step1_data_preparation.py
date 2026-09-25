# -*- coding: utf-8 -*-
"""
مرحله ۱: آماده‌سازی و پاکسازی داده‌های RFM
پروژه: تحلیل رفتار مشتریان بانک توسعه تعاون
نسخه اصلاح‌شده
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
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

# تنظیمات فونت فارسی
matplotlib.rcParams['font.family'] = 'B Nazanin'
plt.rcParams['axes.unicode_minus'] = False

# مسیر فایل
data_path = DATA_RAW_DIR / 'RFM.xlsx'

print("="*80)
print("مرحله ۱: بارگذاری و پاکسازی داده‌های RFM")
print("="*80)

# ==============================================================================
# 1.1 بارگذاری شیت Recency (تازگی)
# ==============================================================================
print("\n📊 شیت 1: Recency (تازگی)")
print("-" * 80)

df_recency_raw = pd.read_excel(data_path, sheet_name='Recency', header=None)
print("ابعاد داده خام:", df_recency_raw.shape)
print("\nنمایش داده خام:")
print(df_recency_raw.to_string())

# استخراج داده‌های مفید (از سطر 2 به بعد که هدر است)
recency_data = {
    'بازه_زمانی': [],
    'حقوقی': [],
    'حقیقی': []
}

# سطرهای 3 تا 8 داده اصلی هستند
for idx in range(3, 9):
    row = df_recency_raw.iloc[idx]
    recency_data['بازه_زمانی'].append(row[1])
    recency_data['حقوقی'].append(int(row[2]) if pd.notna(row[2]) else 0)
    recency_data['حقیقی'].append(int(row[3]) if pd.notna(row[3]) else 0)

df_recency = pd.DataFrame(recency_data)
df_recency['جمع'] = df_recency['حقوقی'] + df_recency['حقیقی']

print("\n✅ داده‌های پاکسازی‌شده Recency:")
print(df_recency.to_string(index=False))

# ==============================================================================
# 1.2 بارگذاری شیت Frequency (تکرار) - فقط سال 1404
# ==============================================================================
print("\n\n📊 شیت 2: Frequency (تکرار) - سال 1404")
print("-" * 80)

df_frequency_raw = pd.read_excel(data_path, sheet_name='Frequency', header=None)

# پیدا کردن ردیف‌های مربوط به سال 1404
frequency_1404_data = {
    'بازه_تراکنش': [],
    'حقیقی': [],
    'حقوقی': []
}

# جستجو در ردیف‌ها برای یافتن سال 1404
start_idx = None
for idx, row in df_frequency_raw.iterrows():
    if pd.notna(row[1]) and '1404' in str(row[1]):
        start_idx = idx
        break

if start_idx:
    # سطر بعد از 1404، داده‌ها شروع می‌شود
    for i in range(1, 9):  # 7 بازه + 1 جمع کل (8 سطر)
        if start_idx + i < len(df_frequency_raw):
            row = df_frequency_raw.iloc[start_idx + i]
            if pd.notna(row[1]):
                frequency_1404_data['بازه_تراکنش'].append(row[1])
                frequency_1404_data['حقیقی'].append(int(row[2]) if pd.notna(row[2]) else 0)
                frequency_1404_data['حقوقی'].append(int(row[3]) if pd.notna(row[3]) else 0)

df_frequency_1404 = pd.DataFrame(frequency_1404_data)
df_frequency_1404['جمع'] = df_frequency_1404['حقیقی'] + df_frequency_1404['حقوقی']

print("\n✅ داده‌های پاکسازی‌شده Frequency (1404):")
print(df_frequency_1404.to_string(index=False))
print(f"\nتعداد ردیف‌های استخراج‌شده: {len(df_frequency_1404)}")

# ==============================================================================
# 1.3 بارگذاری شیت Monetary-Deposite - فقط سال 1404
# ==============================================================================
print("\n\n📊 شیت 3: Monetary-Deposite (سپرده) - سال 1404")
print("-" * 80)

df_monetary_dep_raw = pd.read_excel(data_path, sheet_name='Monetary-Deposite', header=None)

monetary_dep_1404_data = {
    'بازه_مانده': [],
    'حقیقی': [],
    'حقوقی': []
}

# شمارش از انتها
total_rows = len(df_monetary_dep_raw)
# آخرین 8 سطر را می‌گیریم (شامل header + 6 بازه + جمع)
for i in range(total_rows - 8, total_rows - 1):
    row = df_monetary_dep_raw.iloc[i]
    if pd.notna(row[0]) and 'جمع' not in str(row[0]):
        monetary_dep_1404_data['بازه_مانده'].append(row[0])
        monetary_dep_1404_data['حقیقی'].append(int(row[2]) if pd.notna(row[2]) else 0)
        monetary_dep_1404_data['حقوقی'].append(int(row[3]) if pd.notna(row[3]) else 0)

df_monetary_dep_1404 = pd.DataFrame(monetary_dep_1404_data)
df_monetary_dep_1404['جمع'] = df_monetary_dep_1404['حقیقی'] + df_monetary_dep_1404['حقوقی']

print("\n✅ داده‌های پاکسازی‌شده Monetary-Deposite (1404):")
print(df_monetary_dep_1404.to_string(index=False))
print(f"\nتعداد ردیف‌های استخراج‌شده: {len(df_monetary_dep_1404)}")

# ==============================================================================
# 1.4 بارگذاری شیت Tenure (قدمت)
# ==============================================================================
print("\n\n📊 شیت 4: Tenure (قدمت)")
print("-" * 80)

df_tenure_raw = pd.read_excel(data_path, sheet_name='Tenure', header=None)
print("ابعاد داده خام:", df_tenure_raw.shape)

tenure_data = {
    'بازه_قدمت': [],
    'بازه_زمانی': [],
    'حقوقی': [],
    'حقیقی': []
}

# سطرهای 3 تا 9 داده اصلی هستند
for idx in range(3, 10):
    row = df_tenure_raw.iloc[idx]
    if pd.notna(row[0]) and 'جمع' not in str(row[0]):
        tenure_data['بازه_قدمت'].append(row[0])
        tenure_data['بازه_زمانی'].append(row[1])
        tenure_data['حقوقی'].append(int(row[2]) if pd.notna(row[2]) else 0)
        tenure_data['حقیقی'].append(int(row[3]) if pd.notna(row[3]) else 0)

df_tenure = pd.DataFrame(tenure_data)
df_tenure['جمع'] = df_tenure['حقوقی'] + df_tenure['حقیقی']

print("\n✅ داده‌های پاکسازی‌شده Tenure:")
print(df_tenure.to_string(index=False))

# ==============================================================================
# 1.5 بارگذاری شیت Monetary_Loan - فقط سال 1404
# ==============================================================================
print("\n\n📊 شیت 5: Monetary_Loan (تسهیلات) - سال 1404")
print("-" * 80)

df_monetary_loan_raw = pd.read_excel(data_path, sheet_name='Monetary_Loan', header=None)

monetary_loan_1404_data = {
    'بازه_مانده': [],
    'حقیقی': [],
    'حقوقی': []
}

# مشابه Monetary-Deposite، آخرین بلوک را می‌گیریم
total_rows_loan = len(df_monetary_loan_raw)
for i in range(total_rows_loan - 8, total_rows_loan - 1):
    row = df_monetary_loan_raw.iloc[i]
    if pd.notna(row[0]) and 'جمع' not in str(row[0]):
        monetary_loan_1404_data['بازه_مانده'].append(row[0])
        monetary_loan_1404_data['حقیقی'].append(int(row[2]) if pd.notna(row[2]) else 0)
        monetary_loan_1404_data['حقوقی'].append(int(row[3]) if pd.notna(row[3]) else 0)

df_monetary_loan_1404 = pd.DataFrame(monetary_loan_1404_data)
df_monetary_loan_1404['جمع'] = df_monetary_loan_1404['حقیقی'] + df_monetary_loan_1404['حقوقی']

print("\n✅ داده‌های پاکسازی‌شده Monetary_Loan (1404):")
print(df_monetary_loan_1404.to_string(index=False))
print(f"\nتعداد ردیف‌های استخراج‌شده: {len(df_monetary_loan_1404)}")

# ==============================================================================
# ذخیره داده‌های پاکسازی‌شده
# ==============================================================================
output_dir = DATA_PROCESSED_DIR
output_dir.mkdir(exist_ok=True)

print("\n\n" + "="*80)
print("💾 ذخیره داده‌های پاکسازی‌شده")
print("="*80)

# ذخیره در یک فایل Excel با شیت‌های مختلف
output_file = output_dir / 'RFM_Cleaned_Data.xlsx'
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    df_recency.to_excel(writer, sheet_name='Recency', index=False)
    df_frequency_1404.to_excel(writer, sheet_name='Frequency_1404', index=False)
    df_monetary_dep_1404.to_excel(writer, sheet_name='Monetary_Deposit_1404', index=False)
    df_monetary_loan_1404.to_excel(writer, sheet_name='Monetary_Loan_1404', index=False)
    df_tenure.to_excel(writer, sheet_name='Tenure', index=False)

print(f"✅ فایل ذخیره شد: {output_file}")

# ==============================================================================
# ذخیره خلاصه آماری با بررسی امنیت
# ==============================================================================
print("\n" + "="*80)
print("📈 خلاصه آماری داده‌ها")
print("="*80)

# تابع کمکی برای محاسبه ایمن جمع
def safe_sum(df, column_name):
    """محاسبه جمع با بررسی خالی نبودن DataFrame"""
    if len(df) > 0:
        return df[column_name].sum()
    return 0

# تابع کمکی برای دریافت ایمن سطر آخر
def safe_last_row(df, column_name):
    """دریافت مقدار سطر آخر با بررسی خالی نبودن DataFrame"""
    if len(df) > 0:
        return df.iloc[-1][column_name]
    return 0

summary_stats = {
    'معیار': ['Recency', 'Frequency_1404', 'Monetary_Deposit_1404', 
              'Monetary_Loan_1404', 'Tenure'],
    'تعداد_بازه': [
        len(df_recency), 
        len(df_frequency_1404) - 1 if len(df_frequency_1404) > 0 else 0,
        len(df_monetary_dep_1404) - 1 if len(df_monetary_dep_1404) > 0 else 0,
        len(df_monetary_loan_1404) - 1 if len(df_monetary_loan_1404) > 0 else 0,
        len(df_tenure)
    ],
    'جمع_مشتریان_حقیقی': [
        safe_sum(df_recency, 'حقیقی'),
        safe_last_row(df_frequency_1404, 'حقیقی'),
        safe_last_row(df_monetary_dep_1404, 'حقیقی'),
        safe_last_row(df_monetary_loan_1404, 'حقیقی'),
        safe_sum(df_tenure, 'حقیقی')
    ],
    'جمع_مشتریان_حقوقی': [
        safe_sum(df_recency, 'حقوقی'),
        safe_last_row(df_frequency_1404, 'حقوقی'),
        safe_last_row(df_monetary_dep_1404, 'حقوقی'),
        safe_last_row(df_monetary_loan_1404, 'حقوقی'),
        safe_sum(df_tenure, 'حقوقی')
    ]
}

df_summary = pd.DataFrame(summary_stats)
df_summary['جمع_کل'] = df_summary['جمع_مشتریان_حقیقی'] + df_summary['جمع_مشتریان_حقوقی']

print("\n")
print(df_summary.to_string(index=False))

# ذخیره خلاصه
summary_file = output_dir / 'RFM_Summary_Statistics.csv'
df_summary.to_csv(summary_file, index=False, encoding='utf-8-sig')
print(f"\n✅ خلاصه آماری ذخیره شد: {summary_file}")

# ==============================================================================
# بررسی کیفیت داده‌های استخراج‌شده
# ==============================================================================
print("\n" + "="*80)
print("🔍 بررسی کیفیت داده‌های استخراج‌شده")
print("="*80)

quality_check = {
    'DataFrame': ['Recency', 'Frequency_1404', 'Monetary_Deposit_1404', 
                  'Monetary_Loan_1404', 'Tenure'],
    'تعداد_ردیف': [len(df_recency), len(df_frequency_1404), 
                   len(df_monetary_dep_1404), len(df_monetary_loan_1404), 
                   len(df_tenure)],
    'وضعیت': ['✅' if len(df) > 0 else '❌' 
              for df in [df_recency, df_frequency_1404, df_monetary_dep_1404, 
                        df_monetary_loan_1404, df_tenure]]
}

df_quality = pd.DataFrame(quality_check)
print("\n")
print(df_quality.to_string(index=False))

print("\n" + "="*80)
print("✅ مرحله ۱ با موفقیت کامل شد!")
print("="*80)
print("\n📌 فایل‌های خروجی:")
print(f"   1. {output_file}")
print(f"   2. {summary_file}")
print("\n🔜 آماده برای مرحله ۲: تحلیل توزیع‌ها و ترسیم نمودارها")