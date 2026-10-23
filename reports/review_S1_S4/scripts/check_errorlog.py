from pathlib import Path
import os

# Search common SQL Server log paths
paths = [
    Path(r"C:\Program Files\Microsoft SQL Server"),
    Path(r"D:\Program Files\Microsoft SQL Server"),
    Path(r"C:\SQLServer"),
]

for p in paths:
    if p.exists():
        for f in p.rglob("ERRORLOG"):
            print(f"Found log: {f} (size={f.stat().st_size})")
            try:
                with open(f, "r", encoding="utf-16", errors="ignore") as fp:
                    lines = fp.readlines()
                print("Last 10 lines (utf-16):")
                for l in lines[-10:]:
                    print(l.strip())
            except Exception:
                try:
                    with open(f, "r", encoding="utf-8", errors="ignore") as fp:
                        lines = fp.readlines()
                    print("Last 10 lines (utf-8):")
                    for l in lines[-10:]:
                        print(l.strip())
                except Exception as e:
                    print("read err:", e)
