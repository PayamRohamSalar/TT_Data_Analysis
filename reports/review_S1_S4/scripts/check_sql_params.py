import winreg

key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Microsoft SQL Server")
# find instances
try:
    inst_key = winreg.OpenKey(key, "Instance Names\SQL")
    val, _ = winreg.QueryValueEx(inst_key, "MSSQLSERVER")
    print("Instance ID:", val)
    param_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, rf"SOFTWARE\Microsoft\Microsoft SQL Server\{val}\MSSQLServer\Parameters")
    i = 0
    while True:
        try:
            name, value, _ = winreg.EnumValue(param_key, i)
            print(f"Param {name}: {value}")
            i += 1
        except OSError:
            break
except Exception as e:
    print("Error:", e)
