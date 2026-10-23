import pandas as pd
import os
from db_config import get_engine
from sqlalchemy import text

def export_db_samples():
    results_dir = 'results'
    os.makedirs(results_dir, exist_ok=True)
    output_excel = os.path.join(results_dir, "Database_Sample_Export.xlsx")

    print("در حال برقراری ارتباط با دیتابیس...")
    engine = get_engine()
    
    # استخراج لیست تمامی جداول موجود در دیتابیس
    tables_query = """
    SELECT TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_TYPE = 'BASE TABLE' AND TABLE_SCHEMA = 'dbo'
    """
    
    try:
        tables_df = pd.read_sql(tables_query, engine)
        table_names = tables_df['TABLE_NAME'].tolist()
        print(f"تعداد {len(table_names)} جدول در دیتابیس یافت شد.")
    except Exception as e:
        print(f"خطا در خواندن لیست جداول: {e}")
        return

    print(f"در حال استخراج 10 ردیف اول از هر جدول و ذخیره در فایل اکسل...")
    
    # استفاده از ExcelWriter برای نوشتن چندین تب در یک فایل اکسل
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        for table in table_names:
            print(f" - پردازش جدول: {table}")
            
            # کوئری برای گرفتن 10 ردیف اول از هر جدول
            # استفاده از براکت [] برای جلوگیری از خطای نام‌های دارای فاصله یا کاراکتر خاص
            query = f"SELECT TOP 100 * FROM [{table}]"
            
            try:
                # استخراج داده‌ها
                sample_df = pd.read_sql(query, engine)
                
                # نام تب در اکسل نمی‌تواند بیشتر از 31 کاراکتر باشد
                # بنابراین اگر نام جدول طولانی است، آن را کوتاه می‌کنیم
                sheet_name = table[:31] 
                
                # ذخیره داده‌ها در تب مربوطه
                sample_df.to_excel(writer, sheet_name=sheet_name, index=False)
                
            except Exception as e:
                print(f"   ⚠️ خطا در استخراج داده‌های جدول '{table}': {e}")

    print("-" * 50)
    print(f"✅ استخراج با موفقیت انجام شد!")
    print(f"فایل اکسل در مسیر زیر ذخیره شده است:\n{output_excel}")

if __name__ == "__main__":
    export_db_samples()