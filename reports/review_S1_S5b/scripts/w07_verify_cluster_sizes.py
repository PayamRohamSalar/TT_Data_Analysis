import pandas as pd
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

ca = pd.read_pickle('data/processed/phase2_clustering/cluster_assignments_1404.pkl')
print("Columns in cluster_assignments_1404.pkl:", ca.columns.tolist())
print("Total rows:", len(ca))

# Cluster counts for C1-C8
c_counts = ca['cluster'].value_counts().sort_index()
print("\nCluster counts:")
print(c_counts)

claimed = {
    'C1': 67566,
    'C2': 76683,
    'C3': 92179,
    'C4': 30275,
    'C5': 97212,
    'C6': 43250,
    'C7': 44917,
    'C8': 82535
}

res = []
for c_label, c_num in [('C1', 1), ('C2', 2), ('C3', 3), ('C4', 4), ('C5', 5), ('C6', 6), ('C7', 7), ('C8', 8)]:
    actual = int(c_counts.get(c_label, c_counts.get(c_num, 0)))
    exp = claimed[c_label]
    res.append({'cluster': c_label, 'actual': actual, 'claimed': exp, 'diff': actual - exp})

df_res = pd.DataFrame(res)
print("\nComparison:")
print(df_res.to_string(index=False))
print(f"Total C sum actual: {df_res['actual'].sum():,}, claimed: 534,617")

df_res.to_csv('reports/review_S1_S5b/results/w07_cluster_sizes.csv', index=False)
