"""فاز ۲ - الف-۳: جدول مشتری×ماه تسهیلات از Loan_Remain (۶۰ ماه، یک تصویر پایان‌ماه در هر ماه). فقط خواندن؛ یک Engine.
هر طرف قرارداد کل مانده‌ی قرارداد را می‌گیرد (مبنای طرف)؛ مبنای گیرنده‌ی اصلی با vw_Loan_Contract_Dedup مشخص می‌شود؛
قراردادهای بدون رکورد قرارداد جدا شمرده می‌شوند. NPL = Total_Remain - MANDE_JARI (تعریف فاز ۱)."""
from pathlib import Path
import time
import pandas as pd
from tt_bank.db.connection import get_engine
OUT = Path(__file__).resolve().parents[2] / "data" / "processed" / "phase2_clustering"
e = get_engine(); t0 = time.time()
parts, chk = [], []
for y in range(1400, 1405):
    for m in range(1, 13):
        ym = y * 100 + m
        df = pd.read_sql(f"""
        SELECT lr.customer_id, COUNT(*) n_rows,
          SUM(CASE WHEN tot>0 THEN 1 ELSE 0 END) n_party, SUM(tot) bal_party, SUM(tot-jari) npl_party,
          SUM(ov) ov_party, SUM(po) po_party, SUM(db) db_party,
          SUM(CASE WHEN tot>0 AND c.main_customer_id = lr.customer_id THEN 1 ELSE 0 END) n_primary,
          SUM(CASE WHEN c.main_customer_id = lr.customer_id THEN tot ELSE 0 END) bal_primary,
          SUM(CASE WHEN c.main_customer_id = lr.customer_id THEN tot-jari ELSE 0 END) npl_primary,
          SUM(CASE WHEN tot>0 AND c.loanfile_id IS NULL THEN 1 ELSE 0 END) n_nocontract,
          SUM(CASE WHEN c.loanfile_id IS NULL THEN tot ELSE 0 END) bal_nocontract,
          SUM(CASE WHEN tot<0 THEN 1 ELSE 0 END) n_negative,
          SUM(CASE WHEN ABS(tot-(jari+ov+po+db))>1 THEN 1 ELSE 0 END) n_components_mismatch
        FROM (SELECT loanfile_id, customer_id, MAX(Total_Remain) tot, MAX(MANDE_JARI) jari, MAX(Overusance_Remain) ov,
                     MAX(Postponed_Remain) po, MAX(Doubtful_Remain) db
              FROM dbo.Loan_Remain WHERE Transaction_Date BETWEEN {ym*100+1} AND {ym*100+31}
              GROUP BY loanfile_id, customer_id) lr
        LEFT JOIN dbo.vw_Loan_Contract_Dedup c ON c.loanfile_id = lr.loanfile_id
        GROUP BY lr.customer_id""", e)
        df["ym"] = ym
        nn = df[df.customer_id.isna()]
        chk.append((ym, len(df), int(nn.n_rows.sum()), int(df.n_negative.sum()), int(df.n_components_mismatch.sum())))
        df = df[df.customer_id.notna()].copy(); df["customer_id"] = df.customer_id.astype("float64").astype("int64")
        df = df[df.bal_party > 0].drop(columns=["n_negative", "n_components_mismatch", "n_rows"])
        for c in df.columns:
            if c not in ("customer_id", "ym"): df[c] = df[c].astype("float64")
        parts.append(df); print(ym, len(df), f"{time.time()-t0:.0f}s", flush=True)
lm = pd.concat(parts, ignore_index=True)
lm.to_pickle(OUT / "customer_month_loan.pkl")
pd.DataFrame(chk, columns=["ym", "customers_all", "null_customer_rows", "negative_total_rows", "components_mismatch_rows"]).to_csv(OUT / "loan_remain_checks.csv", index=False)
print("done", len(lm))
