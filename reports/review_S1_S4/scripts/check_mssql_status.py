import subprocess

res = subprocess.run(["sc.exe", "query", "MSSQLSERVER"], capture_output=True, text=True)
print(res.stdout)
