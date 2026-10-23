"""فاز ۲ - گام الف-۱: جدول مشتری×ماه سپرده (۱۳۹۹/۰۱ تا ۱۴۰۴/۱۲) به‌صورت pickle (pyarrow نصب نیست). فقط خواندن؛ یک Engine؛ ماه‌به‌ماه.
تکرار محض ردیف‌ها (customer, deposit, month) در همین گام شمرده و با GROUP BY+MAX یکتا می‌شود."""
from pathlib import Path
import time
import pandas as pd
from tt_bank.db.connection import get_engine
OUT = Path(__file__).resolve().parents[2] / "data" / "processed" / "phase2_clustering"
e = get_engine()
parts, dup, null_rows = [], [], []
t0 = time.time()
for y in range(1399, 1405):
    for m in range(1, 13):
        ym = y * 100 + m
        df = pd.read_sql(f"""
        SELECT customer_id, COUNT(*) n_accounts,
               SUM(bal) bal, SUM(cr) cr, SUM(db) db, SUM(crn) crn, SUM(dbn) dbn,
               SUM(raw_rows) raw_rows,
               SUM(CASE WHEN bal<0 THEN 1 ELSE 0 END) neg_acc
        FROM (SELECT customer_id, deposit_id, COUNT(*) raw_rows,
                     MAX(avr_total_amount_eq) bal, MAX(sum_creditor_circul_amount_eq) cr, MAX(sum_debtor_circul_amount_eq) db,
                     MAX(sum_creditor_circul_count) crn, MAX(sum_debtor_circul_count) dbn
              FROM dbo.Deposit_Monthly_Activity WHERE year_mount={ym} GROUP BY customer_id, deposit_id) a
        GROUP BY customer_id""", e)
        df["ym"] = ym
        dup.append((ym, int(df.raw_rows.sum()), int(df.n_accounts.sum())))
        nnull = df[df.customer_id.isna()]
        null_rows.append((ym, int(nnull.n_accounts.sum()), float(nnull.bal.fillna(0).sum())))
        df = df[df.customer_id.notna()].copy()
        df["customer_id"] = df.customer_id.astype("float64").astype("int64")
        for c in ["bal", "cr", "db", "crn", "dbn"]:
            df[c] = df[c].astype("float64")
        parts.append(df.drop(columns=["raw_rows"]))
        print(ym, len(df), f"{time.time()-t0:.0f}s", flush=True)
cm = pd.concat(parts, ignore_index=True)
cm.to_pickle(OUT / "customer_month_deposit.pkl")
pd.DataFrame(dup, columns=["ym", "raw_rows", "unique_account_rows"]).to_csv(OUT / "dma_duplicate_check.csv", index=False)
pd.DataFrame(null_rows, columns=["ym","null_customer_account_rows","null_customer_balance"]).to_csv(OUT / "dma_null_customer_check.csv", index=False)
print("done", len(cm))
