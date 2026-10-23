import subprocess
import sys

res = subprocess.run(["sc.exe", "query", "state=", "all"], capture_output=True, text=True)
lines = [l for l in res.stdout.splitlines() if "SQL" in l.upper() or "MSSQL" in l.upper()]
for l in lines:
    print(l)
