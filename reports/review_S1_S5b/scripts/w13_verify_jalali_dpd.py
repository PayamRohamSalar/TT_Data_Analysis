import time
import datetime
from sqlalchemy import text
from tt_bank.db.connection import get_engine
import pandas as pd
import numpy as np
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

t0 = time.time()
engine = get_engine()

# Independent Jalali to Gregorian converter (pure math, no 3rd party packages)
def jalali_to_gregorian(jy, jm, jd):
    jy += 1595
    days = -355668 + (365 * jy) + ((jy // 33) * 8) + (((jy % 33) + 3) // 4) + jd
    if jm < 7:
        days += (jm - 1) * 31
    else:
        days += ((jm - 7) * 30) + 186
    gy = 400 * (days // 146097)
    days %= 146097
    if days > 36524:
        days -= 1
        gy += 100 * (days // 36524)
        days %= 36524
        if days >= 365:
            days += 1
    gy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        days -= 1
        gy += (days // 365)
        days %= 365
    gd = days + 1
    sal_a = [0, 31, ((gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0)) and 29 or 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    gm = 0
    while gm < 13 and gd > sal_a[gm]:
        gd -= sal_a[gm]
        gm += 1
    return datetime.date(gy, gm, gd)

def parse_and_diff_dates(d_str, p_str):
    try:
        dy, dm, dd = [int(x) for x in d_str.strip().split('/')]
        py, pm, pd_ = [int(x) for x in p_str.strip().split('/')]
        g_due = jalali_to_gregorian(dy, dm, dd)
        g_paid = jalali_to_gregorian(py, pm, pd_)
        return (g_paid - g_due).days
    except Exception:
        return np.nan

print("Querying 10,000 installment sample from Loan_Monthly_Activity...")
# SQL query using exact Jalali formula as in 06b_
CD = "LTRIM(RTRIM(REPLACE({c}, CHAR(34), '')))"
dd, pdt = CD.format(c="delivery_date"), CD.format(c="payed_date")

def ordn(x):
    Y = f"TRY_CAST(LEFT({x},4) AS int)"
    Mo = f"TRY_CAST(SUBSTRING({x},6,2) AS int)"
    Da = f"TRY_CAST(SUBSTRING({x},9,2) AS int)"
    r = f"(({Y}-1)%33)"
    leap = " + ".join(f"CASE WHEN {r}>={t} THEN 1 ELSE 0 END" for t in (1, 5, 9, 13, 17, 22, 26, 30))
    cum = f"CASE WHEN {Mo}<=6 THEN ({Mo}-1)*31 ELSE 186+({Mo}-7)*30 END"
    return f"(({Y}-1)*365 + (({Y}-1)/33)*8 + {leap} + {cum} + {Da})"

q = f"""
SELECT TOP 10000 
    {dd} as delivery_date,
    {pdt} as payed_date,
    {ordn(dd)} as due_ord,
    {ordn(pdt)} as paid_ord,
    ({ordn(pdt)} - {ordn(dd)}) as sql_dpd
FROM dbo.Loan_Monthly_Activity
WHERE {dd} LIKE '1403/%'
"""
sample_df = pd.read_sql(q, engine)
print(f"Sample retrieved: {len(sample_df)} rows ({time.time()-t0:.1f}s)")

# Check missing payed_date in sample
null_paid = sample_df['payed_date'].isna() | (sample_df['payed_date'] == '')
print(f"Null/empty payed_date in sample: {null_paid.sum()}")

# Calculate independent Python Gregorian difference
sample_df['py_dpd'] = [parse_and_diff_dates(r.delivery_date, r.payed_date) for _, r in sample_df.iterrows()]

# Compare sql_dpd vs py_dpd
diff = (sample_df['sql_dpd'] - sample_df['py_dpd']).abs()
print(f"Max difference between SQL Jalali formula and independent Gregorian conversion: {diff.max()}")
print(f"Number of rows with diff == 0: {(diff == 0).sum()} / {len(sample_df)}")

# Now let's check overall percentages in customer_month_ledger_exact.pkl or sample
# Let's inspect customer_month_ledger_exact.pkl
print("\nLoading customer_month_ledger_exact.pkl...")
t1 = time.time()
lg = pd.read_pickle('data/processed/phase2_clustering/customer_month_ledger_exact.pkl')
print(f"Loaded ledger exact: {len(lg):,} rows ({time.time()-t1:.1f}s)")

# Calculate overall rates
n_inst_total = lg['n_inst'].sum()
n_paid_total = lg['n_paid'].sum()
n_late_total = lg['n_late'].sum()
n_late30_total = lg['n_late30'].sum()
n_late90_total = lg['n_late90'].sum()
n_unpaid_total = lg['n_unpaid'].sum()

print("\n--- Aggregate Metrics across ALL installments in ledger exact ---")
print(f"Total installments: {n_inst_total:,}")
print(f"Total paid installments: {n_paid_total:,} ({n_paid_total/n_inst_total*100:.2f}%)")
print(f"Total unpaid installments: {n_unpaid_total:,} ({n_unpaid_total/n_inst_total*100:.2f}%)")
print(f"Any delay (> 0 days): {n_late_total:,} ({n_late_total/n_inst_total*100:.2f}%, Claimed: 57.9%)")
print(f"Delay > 30 days: {n_late30_total:,} ({n_late30_total/n_inst_total*100:.2f}%, Claimed: 28.7%)")
print(f"Delay > 90 days: {n_late90_total:,} ({n_late90_total/n_inst_total*100:.2f}%, Claimed: 6.9%)")

res_w13 = pd.DataFrame([{
    'metric': 'any_delay_pct', 'reproduced': round(n_late_total/n_inst_total*100, 2), 'claimed': 57.9
}, {
    'metric': 'delay_gt_30_pct', 'reproduced': round(n_late30_total/n_inst_total*100, 2), 'claimed': 28.7
}, {
    'metric': 'delay_gt_90_pct', 'reproduced': round(n_late90_total/n_inst_total*100, 2), 'claimed': 6.9
}, {
    'metric': 'all_have_payed_date', 'reproduced': (n_unpaid_total == 0), 'claimed': True
}])
res_w13.to_csv('reports/review_S1_S5b/results/w13_jalali_dpd_reproduction.csv', index=False)
sample_df.head(100).to_csv('reports/review_S1_S5b/results/w13_sample_100_dpd_compare.csv', index=False)
print("Saved W13 results.")
