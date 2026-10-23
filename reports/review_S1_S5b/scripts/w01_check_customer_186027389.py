import os
import glob
import re
import sys
import csv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

files_to_check = []
for ext in ['*.md', '*.txt']:
    files_to_check.extend(glob.glob(f'reports/**/{ext}', recursive=True))
    files_to_check.extend(glob.glob(f'docs/**/{ext}', recursive=True))

results = []
for fpath in files_to_check:
    if 'review_S1_S5b' in fpath:
        continue
    try:
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            for idx, line in enumerate(f, 1):
                if '186027389' in line:
                    results.append((fpath, idx, line.strip()))
    except Exception as e:
        results.append((fpath, 0, f"ERROR: {e}"))

out_path = 'reports/review_S1_S5b/results/w01_customer_186027389_search.csv'
with open(out_path, 'w', encoding='utf-8-sig', newline='') as out:
    w = csv.writer(out)
    w.writerow(['file', 'line_num', 'line_content'])
    for r in results:
        w.writerow(r)

print(f"Found {len(results)} occurrences across documents.")
for r in results:
    print(f"{r[0]}:{r[1]} -> {r[2][:120]}")
