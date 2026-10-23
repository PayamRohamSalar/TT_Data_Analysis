import pandas as pd

pan = pd.read_pickle("data/processed/phase2_clustering/panel_customer_year.pkl")
c_186 = pan[pan["customer_id"] == 186027389]
print("Customer 186027389 in panel_customer_year.pkl:")
print(c_186[["customer_id", "y", "months", "nacc_max", "bal_mean", "bal_dec", "category"]])

c_186.to_csv("reports/review_S1_S4/results/v8_customer_186027389_in_panel.csv", index=False)
