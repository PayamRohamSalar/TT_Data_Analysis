import pandas as pd
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

pan = pd.read_pickle('data/processed/phase2_clustering/panel_customer_year.pkl')
p1404 = pan[pan['y'] == 1404].copy()
model_mask = (p1404['category'] == 'model')
primary_mask = model_mask & p1404['has_primary_loan']

grid_results = []
turn_thresholds = [2, 3, 4]
bal_thresholds = [2e6, 5e6, 10e6]

for tm in turn_thresholds:
    for bm in bal_thresholds:
        t_mask = primary_mask & ((p1404['turn_months'] < tm) | (p1404['bal_max'] < bm))
        count_t = int(t_mask.sum())
        count_main = int(model_mask.sum() - count_t)
        share_t = count_t / model_mask.sum() * 100
        grid_results.append({
            'turn_months_threshold': tm,
            'bal_max_threshold_M_Rls': bm / 1e6,
            'count_T': count_t,
            'count_main': count_main,
            'share_T_pct': round(share_t, 2)
        })

df_grid = pd.DataFrame(grid_results)
print("--- Sensitivity Grid for Group T (Year 1404) ---")
print(df_grid.to_string(index=False))
df_grid.to_csv('reports/review_S1_S5b/results/w06_group_t_sensitivity.csv', index=False)
