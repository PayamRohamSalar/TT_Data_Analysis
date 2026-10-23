from pathlib import Path

p = Path("data/processed/phase2_clustering/s4_labels")
for f in sorted(p.glob("*.npy")):
    print(f.name, f.stat().st_size)
