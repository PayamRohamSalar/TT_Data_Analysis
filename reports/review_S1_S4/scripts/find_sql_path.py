import winreg

def find_sql():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\MSSQLSERVER")
        val, _ = winreg.QueryValueEx(key, "ImagePath")
        print(f"MSSQLSERVER ImagePath: {val}")
    except Exception as e:
        print("Registry error:", e)

find_sql()
