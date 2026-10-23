from pathlib import Path

p = Path("data/processed/phase2_clustering")
if p.exists():
    for f in sorted(p.iterdir()):
        print(f"{f.name}: {f.stat().st_size / (1024*1024):.2f} MB")
else:
    print("Not found")
