import urllib
from sqlalchemy import create_engine

# تنظیمات پایه سرور
# اگر در اتصال خطایی دریافت کردید، 'localhost' را به '.\\SQLEXPRESS' تغییر دهید
SERVER_NAME = 'localhost'  
DATABASE_NAME = 'Alzahra'

# ایجاد رشته اتصال امن (استفاده از Windows Authentication)
connection_string = (
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    rf'SERVER={SERVER_NAME};'
    rf'DATABASE={DATABASE_NAME};'
    r'Trusted_Connection=yes;'
)

# رمزگذاری رشته اتصال برای استفاده در SQLAlchemy
params = urllib.parse.quote_plus(connection_string)
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

def get_engine():
    """
    این تابع را در هر فایلی فراخوانی کنید، موتور اتصال به دیتابیس را برمی‌گرداند.
    """
    return engine