import pandas as pd
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

s5_pop = pd.read_csv('data/processed/phase2_clustering/s5_population.csv')
print("--- s5_population.csv ---")
print(s5_pop.to_string())

# Now let's verify panel_customer_year.pkl for 1404 directly
pan = pd.read_pickle('data/processed/phase2_clustering/panel_customer_year.pkl')
p1404 = pan[pan['y'] == 1404].copy()

counts = p1404['category'].value_counts()
print("\nPanel 1404 categories:")
for k, v in counts.items():
    print(f"  {k}: {v:,}")

# Check token borrowers
# Rule: category == 'model' & has_primary_loan & (turn_months < 3 | bal_max < 5e6)
p1404['is_T'] = (p1404['category'] == 'model') & p1404['has_primary_loan'] & ((p1404['turn_months'] < 3) | (p1404['bal_max'] < 5e6))
nT = p1404['is_T'].sum()
nModel = (p1404['category'] == 'model').sum()
nMain = nModel - nT
print(f"\nModel total: {nModel:,}")
print(f"Group T (token borrowers): {nT:,}")
print(f"Main clustering population (Model - T): {nMain:,}")

# Let's save the exact numbers to CSV
res_w5 = pd.DataFrame([
    {'group': 'model_all', 'count': nModel},
    {'group': 'idle_token', 'count': counts.get('idle_token', 0)},
    {'group': 'newcomer', 'count': counts.get('newcomer', 0)},
    {'group': 'institutional_candidate', 'count': counts.get('institutional_candidate', 0)},
    {'group': 'partial_other', 'count': counts.get('partial_other', 0)},
    {'group': 'group_T', 'count': nT},
    {'group': 'main_population', 'count': nMain},
    {'group': 'total_panel_1404', 'count': len(p1404)}
])
res_w5.to_csv('reports/review_S1_S5b/results/w05_population_counts.csv', index=False)
print("\nSaved to reports/review_S1_S5b/results/w05_population_counts.csv")
