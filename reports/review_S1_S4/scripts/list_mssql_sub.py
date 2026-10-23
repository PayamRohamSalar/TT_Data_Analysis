from pathlib import Path

base = Path(r"C:\Program Files\Microsoft SQL Server\MSSQL17.MSSQLSERVER\MSSQL")
for p in base.iterdir():
    print(p)
