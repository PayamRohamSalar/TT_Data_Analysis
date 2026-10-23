"""فاز ۲ - S2: استخراج ورودی‌های DB برای ذخیره‌ی ویژگی (فقط خواندن؛ یک Engine؛ ترتیبی).
(الف) مانده‌ی هر نوع حساب هر مشتری در 12 هر سال؛ (ب) تصویر قرارداد-سطح 12/1401 و 12/1402؛ (ج) کارمزد مشتری-سال-کد؛
(د) تاریخ نخستین حساب و حساب‌های مسدود؛ (ه) شعبه‌ی خانه."""
from pathlib import Path
import time
import numpy as np, pandas as pd
from tt_bank.db.connection import get_engine
D = Path(__file__).resolve().parents[2] / "data" / "processed" / "phase2_clustering"
e = get_engine(); q = lambda s: pd.read_sql(s, e); t0 = time.time()
def tick(m): print(f"{m} {time.time()-t0:.0f}s", flush=True)

# (الف)
for ym in (140012, 140112, 140212, 140312):
    t = q(f"""SELECT d.customer_id, ISNULL(a.deposit_type, N'unknown') typ, COUNT(*) n_acc, SUM(d.bal) bal
             FROM (SELECT customer_id, deposit_id, MAX(avr_total_amount_eq) bal FROM dbo.Deposit_Monthly_Activity WHERE year_mount={ym} GROUP BY customer_id, deposit_id) d
             LEFT JOIN dbo.vw_Deposit_Account_Dedup a ON a.deposit_id = d.deposit_id
             GROUP BY d.customer_id, ISNULL(a.deposit_type, N'unknown')""")
    t = t[t.customer_id.notna()].copy(); t["customer_id"] = t.customer_id.astype("float64").astype("int64")
    t.to_pickle(D / f"deposit_type_balance_{ym}.pkl"); tick(f"type balance {ym} rows {len(t)}")

# (ب)
for ym in (140112, 140212):
    r = q(f"""SELECT loanfile_id, customer_id, MAX(LTRIM(RTRIM(REPLACE(ECO_SEC,CHAR(34),'')))) eco, MAX(Total_Remain) tot, MAX(MANDE_JARI) jari
              FROM dbo.Loan_Remain WHERE Transaction_Date BETWEEN {ym*100+1} AND {ym*100+31} GROUP BY loanfile_id, customer_id""")
    r.to_pickle(D / f"loan_remain_{ym}.pkl"); tick(f"loan_remain {ym} rows {len(r)}")

# (ج)
f = q("""SELECT main_customer_id c, year_mount ym, REPLACE(code, CHAR(34), '') code, COUNT(*) n, SUM(amount_eq) amt
         FROM (SELECT DISTINCT main_customer_id, year_mount, code, amount_eq FROM dbo.Customer_Monthly_Activity) x
         GROUP BY main_customer_id, year_mount, REPLACE(code, CHAR(34), '')""")
f = f[f.c.notna()].copy(); f["c"] = f.c.astype("float64").astype("int64")
f.to_pickle(D / "fee_customer_month_code.pkl"); tick(f"fees rows {len(f)}")

# (د)
a = q("""SELECT CAST(LTRIM(RTRIM(MAIN_CUSTOMER_ID)) AS bigint) c, LTRIM(RTRIM(OPEN_DATE)) od, LTRIM(RTRIM(STATUS_NAME)) st
         FROM dbo.Deposit_Accoutnt_Info WHERE ISNUMERIC(LTRIM(RTRIM(MAIN_CUSTOMER_ID)))=1""")
a.to_pickle(D / "account_open_status.pkl"); tick(f"accounts rows {len(a)}")

# (ه)
h = q("SELECT CAST(customer_id AS bigint) c, branch_code, source FROM dbo.Dim_Customer_Home_Branch")
h.to_pickle(D / "home_branch.pkl"); tick(f"home branch rows {len(h)}")
print("done")
