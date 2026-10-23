import pandas as pd
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

rank = pd.read_csv('data/processed/phase2_clustering/s4b_method_ranking_v2.csv')
print("--- s4b_method_ranking_v2.csv ---")
print(rank.to_string())

scores = pd.read_csv('data/processed/phase2_clustering/s4b_scores_by_k.csv')
print("\n--- s4b_scores_by_k.csv ---")
print(scores.to_string())

rank.to_csv('reports/review_S1_S5b/results/w03_s4b_ranking_check.csv', index=False)
