import os
import glob
import re
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

for p in glob.glob('notebooks/phase2_clustering/*.py'):
    with open(p, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
        if '315' in text or 'np==1' in text or 'np == 1' in text or 'inferred' in text:
            print(f"Match in {p}")
