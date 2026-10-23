"""فاز ۲ - الف-۳: ویژگی‌های دفتر اقساط (Loan_Monthly_Activity) در سطح گیرنده‌ی اصلی×ماه‌ی سررسید. فقط خواندن؛ یک Engine.
DPD تقریبی: (سال*372+ماه*31+روز) پرداخت منهای سررسید؛ برای دیرکردهای کوتاه (کمتر از چند ماه) خطا کمتر از یک روز است.
قراردادهای بدون رکورد قرارداد (بدون گیرنده‌ی اصلی) در شمارش پوشش می‌آیند و در ویژگی‌ها نمی‌آیند."""
from pathlib import Path
import time
import pandas as pd
from tt_bank.db.connection import get_engine
OUT = Path(__file__).resolve().parents[2] / "data" / "processed" / "phase2_clustering"
e = get_engine(); t0 = time.time()
CD = "LTRIM(RTRIM(REPLACE({c}, CHAR(34), '')))"
dd, pdt = CD.format(c="m.delivery_date"), CD.format(c="m.payed_date")
def ordn(x): return f"(TRY_CAST(LEFT({x},4) AS int)*372 + TRY_CAST(SUBSTRING({x},6,2) AS int)*31 + TRY_CAST(SUBSTRING({x},9,2) AS int))"
parts, cov = [], []
for y in range(1400, 1405):
    sql = f"""
    SELECT c.main_customer_id cid, due_ym, COUNT(*) n_inst,
      SUM(CASE WHEN paid_ord IS NOT NULL THEN 1 ELSE 0 END) n_paid,
      SUM(CASE WHEN paid_ord IS NOT NULL AND paid_ord-due_ord>0 THEN 1 ELSE 0 END) n_late,
      SUM(CASE WHEN paid_ord IS NOT NULL AND paid_ord-due_ord>30 THEN 1 ELSE 0 END) n_late30,
      SUM(CASE WHEN paid_ord IS NOT NULL AND paid_ord-due_ord>90 THEN 1 ELSE 0 END) n_late90,
      SUM(CASE WHEN paid_ord IS NULL THEN 1 ELSE 0 END) n_unpaid,
      MAX(CASE WHEN paid_ord IS NOT NULL THEN paid_ord-due_ord END) max_dpd,
      SUM(CASE WHEN paid_ord IS NOT NULL THEN paid_ord-due_ord ELSE 0 END) sum_dpd,
      SUM(imain) s_main, SUM(iint) s_int, SUM(ipen) s_pen,
      SUM(CASE WHEN st='moaavagh' THEN 1 ELSE 0 END) n_moaavagh,
      SUM(CASE WHEN st='mashkoo' THEN 1 ELSE 0 END) n_mashkoo,
      SUM(CASE WHEN st='sar resid ghozashte' THEN 1 ELSE 0 END) n_sarresid_past
    FROM (SELECT m.loanfile_id, m.installment_main imain, m.installment_interest iint, m.installment_penalty ipen,
                 LTRIM(RTRIM(REPLACE(m.Status, CHAR(34), ''))) st,
                 TRY_CAST(REPLACE(LEFT({dd},7),'/','') AS int) due_ym, {ordn(dd)} due_ord,
                 CASE WHEN LEN({pdt})>=10 THEN {ordn(pdt)} END paid_ord
          FROM dbo.Loan_Monthly_Activity m WHERE {dd} LIKE '{y}/%') x
    JOIN dbo.vw_Loan_Contract_Dedup c ON c.loanfile_id = x.loanfile_id
    GROUP BY c.main_customer_id, due_ym"""
    df = pd.read_sql(sql, e)
    tot = pd.read_sql(f"SELECT COUNT(*) n, SUM(CASE WHEN c.loanfile_id IS NOT NULL THEN 1 ELSE 0 END) linked FROM dbo.Loan_Monthly_Activity m LEFT JOIN dbo.vw_Loan_Contract_Dedup c ON c.loanfile_id=m.loanfile_id WHERE {dd} LIKE '{y}/%'", e)
    cov.append((y, int(tot.n[0]), int(tot.linked[0]), len(df)))
    parts.append(df); print(y, len(df), cov[-1], f"{time.time()-t0:.0f}s", flush=True)
lg = pd.concat(parts, ignore_index=True)
lg.to_pickle(OUT / "customer_month_ledger.pkl")
pd.DataFrame(cov, columns=["year", "ledger_rows_due_in_year", "rows_linked_to_contract", "customer_month_rows"]).to_csv(OUT / "ledger_year_coverage.csv", index=False)
print("done", len(lg))
