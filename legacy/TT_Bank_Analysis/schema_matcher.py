import pandas as pd
import os
from db_config import get_engine
from datetime import datetime

def match_schema():
    # ۱. تنظیم مسیر پوشه‌ها و فایل‌ها
    data_dir = 'data'
    results_dir = 'results'
    
    # در صورت عدم وجود پوشه‌ها، آن‌ها را ایجاد می‌کند
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)
    
    excel_file = os.path.join(data_dir, "Data_Required_R6_Monthly.xlsx")
    output_file = os.path.join(results_dir, "Schema_Matching_Report.txt")

    # متغیری برای ذخیره متن گزارش
    report_lines = []
    
    report_lines.append("گزارش تطبیق جداول دیتابیس با نیازمندی‌های پروژه")
    report_lines.append("=" * 60)
    report_lines.append(f"تاریخ و زمان اجرا: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("-" * 60 + "\n")

    print(f"در حال خواندن فایل نیازمندی‌ها از مسیر: {excel_file}...")
    try:
        required_data = pd.read_excel(excel_file, sheet_name=None)
    except FileNotFoundError:
        error_msg = f"خطا: فایل اکسل در مسیر '{excel_file}' پیدا نشد. لطفاً مطمئن شوید فایل در پوشه data قرار دارد."
        print(error_msg)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(error_msg)
        return

    print("در حال برقراری ارتباط با دیتابیس و استخراج متادیتا...")
    engine = get_engine()
    
    query = """
    SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE 
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'dbo'
    """
    db_schema = pd.read_sql(query, engine)
    db_tables = db_schema['TABLE_NAME'].unique()
    
    report_lines.append(f"تعداد کل جداول یافت شده در دیتابیس: {len(db_tables)}\n")
    report_lines.append("جزئیات تطبیق به تفکیک هر جدول:")
    report_lines.append("=" * 60 + "\n")

    for sheet_name, df in required_data.items():
        report_lines.append(f"### نیازمندی: تب [{sheet_name}]")
        required_columns = set(df.columns)
        
        matching_tables = db_schema[db_schema['TABLE_NAME'].str.contains(sheet_name, case=False, na=False)]
        
        if not matching_tables.empty:
            actual_table = matching_tables['TABLE_NAME'].iloc[0]
            actual_columns = set(db_schema[db_schema['TABLE_NAME'] == actual_table]['COLUMN_NAME'])
            
            available_cols = required_columns.intersection(actual_columns)
            missing_cols = required_columns - actual_columns
            
            report_lines.append(f"✔️ وضعیت: جدول معادل در دیتابیس یافت شد -> '{actual_table}'")
            report_lines.append(f"📊 فیلدهای منطبق: {len(available_cols)} از {len(required_columns)}")
            
            if missing_cols:
                report_lines.append("⚠️ فیلدهای مفقود در دیتابیس:")
                for col in sorted(missing_cols):
                    report_lines.append(f"   - {col}")
            else:
                report_lines.append("✅ تمامی فیلدهای مورد نیاز در این جدول موجود است.")
        else:
            report_lines.append("❌ وضعیت: هیچ جدولی با نام مشابه در دیتابیس یافت نشد.")
            report_lines.append(f"   - فیلدهای درخواستی: {', '.join(required_columns)}")
            
        report_lines.append("\n" + "-" * 40 + "\n")

    # ۲. ذخیره گزارش در فایل متنی
    print(f"\nتطبیق پایان یافت. در حال ذخیره گزارش در مسیر: {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
        
    print("عملیات با موفقیت انجام شد! فایل گزارش آماده بررسی است.")

if __name__ == "__main__":
    match_schema()