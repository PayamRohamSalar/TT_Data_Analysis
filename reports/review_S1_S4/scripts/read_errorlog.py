from pathlib import Path

p = Path(r"C:\Program Files\Microsoft SQL Server\MSSQL17.MSSQLSERVER\MSSQL\Log\ERRORLOG")
if p.exists():
    print(f"Log exists, size={p.stat().st_size}")
    try:
        with open(p, "r", encoding="utf-16le", errors="ignore") as f:
            lines = f.readlines()
        print("Last 25 lines:")
        for l in lines[-25:]:
            print(l.strip())
    except Exception as e:
        print("read error:", e)
else:
    print("Does not exist")
