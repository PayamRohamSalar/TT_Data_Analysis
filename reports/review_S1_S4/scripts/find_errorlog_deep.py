from pathlib import Path

base = Path(r"C:\Program Files\Microsoft SQL Server\MSSQL17.MSSQLSERVER")
if base.exists():
    for x in base.rglob("*"):
        if "ERRORLOG" in x.name.upper() or x.name.endswith(".log"):
            print(x)
