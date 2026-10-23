from pathlib import Path

base = Path(r"C:\Program Files\Microsoft SQL Server\MSSQL17.MSSQLSERVER")
for p in base.iterdir():
    print(p)
