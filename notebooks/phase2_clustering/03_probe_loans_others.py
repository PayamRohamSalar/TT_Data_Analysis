"""فاز ۲ - الف-۳/۴: بررسی تسهیلات، کارمزد، سود پرداختی، نوع حساب، شعبه‌ی خانه، پروفایل (فقط خواندن؛ یک Engine)."""
from pathlib import Path
import numpy as np, pandas as pd
from tt_bank.db.connection import get_engine
D = Path(__file__).resolve().parents[2] / "data" / "processed" / "phase2_clustering"
e = get_engine(); q = lambda s: pd.read_sql(s, e)
log = []
def p(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); log.append(s)
def save():
    (D / "probe_loans_others.txt").write_text("\n".join(log), encoding="utf-8")

# ---- ساختار زمانی Loan_Remain
t = q("""SELECT Transaction_Date/100 ym, COUNT(DISTINCT Transaction_Date) n_dates, COUNT(*) n_rows,
         MIN(Transaction_Date) mn, MAX(Transaction_Date) mx FROM dbo.Loan_Remain GROUP BY Transaction_Date/100 ORDER BY 1""")
t.to_csv(D / "loan_remain_dates_by_month.csv", index=False)
p("Loan_Remain months:", len(t), "range", int(t.ym.min()), int(t.ym.max()), " dates/month median", t.n_dates.median(), "max", t.n_dates.max())
p(t[t.ym >= 140401].to_string())
save()
