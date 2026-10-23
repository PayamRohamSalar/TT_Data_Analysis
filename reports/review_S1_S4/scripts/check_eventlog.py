import subprocess

ps_script = """
Get-WinEvent -FilterHashtable @{LogName='Application'; ProviderName='MSSQLSERVER'} -MaxEvents 5 | Format-List TimeCreated, Id, Message
"""

res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True)
print("STDOUT:")
print(res.stdout)
print("STDERR:")
print(res.stderr)
