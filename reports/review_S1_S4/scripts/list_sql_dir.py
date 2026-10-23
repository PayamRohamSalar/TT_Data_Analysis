from pathlib import Path

base = Path(r"C:\Program Files\Microsoft SQL Server")
for p in base.iterdir():
    print(p)
