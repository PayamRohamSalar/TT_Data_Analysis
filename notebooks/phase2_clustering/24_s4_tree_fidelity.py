"""فاز ۲ - S4: وفاداری درخت جانشین (عمق 4) برای هر (روش، k): معیار تفسیرپذیری قابل‌بیان با قاعده (بدون DB)."""
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.tree import DecisionTreeClassifier
from tt_bank.phase2_clustering.prep import Prep
D = Path(__file__).resolve().parents[2] / "data" / "processed" / "phase2_clustering"; LAB = D / "s4_labels"
F = pd.read_pickle(D / "features_customer_year.pkl"); A = F[(F.category == "model") & (F.y == 1404)].reset_index(drop=True)
prep = Prep.from_json(D / "prep_spec.json"); X = prep.transform(A)
R = pd.read_csv(D / "s4_scorecard_raw.csv"); rng = np.random.default_rng(0)
idx = rng.permutation(len(X)); tr, te = idx[: int(.6 * len(X))], idx[int(.6 * len(X)):]
rows = []
for r in R.itertuples():
    f = LAB / f"{r.method}_k{int(r.k)}_A.npy"
    if not f.exists(): f = LAB / f"{r.method}_kNA_A.npy"
    if not f.exists(): continue
    y = np.load(f)
    t = DecisionTreeClassifier(max_depth=4, random_state=0).fit(X[tr], y[tr])
    rows.append(dict(method=r.method, k=r.k, fidelity=float((t.predict(X[te]) == y[te]).mean())))
    print(rows[-1], flush=True)
pd.DataFrame(rows).to_csv(D / "s4_tree_fidelity.csv", index=False)
