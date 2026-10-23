import pandas as pd
import os
from db_config import get_engine

def summarize_database():
    # اطمینان از وجود پوشه نتایج
    results_dir = 'results'
    os.makedirs(results_dir, exist_ok=True)
    output_excel = os.path.join(results_dir, "Database_Summary.xlsx")

    print("در حال برقراری ارتباط با دیتابیس...")
    engine = get_engine()
    
    # ۱. استخراج لیست تمامی جداول موجود
    tables_query = """
    SELECT TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_TYPE = 'BASE TABLE' AND TABLE_SCHEMA = 'dbo'
    """
    
    try:
        tables_df = pd.read_sql(tables_query, engine)
        table_names = tables_df['TABLE_NAME'].tolist()
        print(f"تعداد {len(table_names)} جدول برای پردازش یافت شد.\n")
    except Exception as e:
        print(f"❌ خطا در خواندن لیست جداول: {e}")
        return

    summary_data = []
    
    # ۲. محاسبه تعداد ردیف و ستون برای هر جدول
    print("در حال محاسبه آمار جداول (این عملیات ممکن است بسته به حجم داده‌ها چند ثانیه طول بکشد)...")
    
    for table in table_names:
        print(f" - در حال پردازش جدول: {table}")
        
        # کوئری برای گرفتن تعداد ستون‌ها از متادیتا (بسیار سریع)
        cols_query = f"""
        SELECT COUNT(*) as col_count 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = '{table}' AND TABLE_SCHEMA = 'dbo'
        """
        
        # کوئری برای گرفتن تعداد ردیف‌ها
        rows_query = f"SELECT COUNT(*) as row_count FROM [{table}]"
        
        try:
            col_count = pd.read_sql(cols_query, engine).iloc[0]['col_count']
            row_count = pd.read_sql(rows_query, engine).iloc[0]['row_count']
            
            summary_data.append({
                'نام جدول (Table Name)': table,
                'تعداد ستون‌ها (Columns Count)': col_count,
                'تعداد ردیف‌ها (Rows Count)': f"{row_count:,}"  # جداکننده هزارگان برای خوانایی بهتر
            })
        except Exception as e:
            print(f"   ⚠️ خطا در استخراج آمار جدول '{table}': {e}")

    # ۳. تبدیل به دیتافریم و ذخیره در اکسل
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        
        # مرتب‌سازی جداول بر اساس نام
        summary_df = summary_df.sort_values(by='نام جدول (Table Name)')
        
        try:
            summary_df.to_excel(output_excel, index=False, engine='openpyxl')
            print("-" * 50)
            print(f"✅ خلاصه وضعیت دیتابیس با موفقیت استخراج شد!")
            print(f"فایل گزارش در مسیر زیر ذخیره شده است:\n{output_excel}")
        except Exception as e:
            print(f"❌ خطا در ذخیره فایل اکسل: {e}")
    else:
        print("داده‌ای برای ذخیره یافت نشد.")

if __name__ == "__main__":
    summarize_database()