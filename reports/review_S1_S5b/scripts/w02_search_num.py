import os
import glob
import re

for root, dirs, files in os.walk('.'):
    if 'review_S1_S5b' in root:
        continue
    for file in files:
        if file.endswith('.py') or file.endswith('.sql') or file.endswith('.log') or file.endswith('.txt'):
            p = os.path.join(root, file)
            try:
                with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if '146473' in content or '146,473' in content or '315146' in content or '315,146' in content:
                        print(f"Found in {p}")
            except Exception:
                pass
