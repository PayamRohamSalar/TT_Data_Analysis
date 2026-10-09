"""میانگین ماهانه‌ی مانده‌ی قراردادهای دارای دفتر اقساط (Loan_Monthly_Activity) به تفکیک سال ۱۴۰۰ تا ۱۴۰۴؛ مخرج بازده دریافتی.
خروجی: data/processed/phase1_market_overview/ledger_coverage_by_year.csv   (فقط یک Engine؛ python -u مستقیم)"""
from pathlib import Path

import pandas as pd

from tt_bank.db.connection import get_engine

OUT = Path(__file__).resolve().parents[2] / "data" / "processed" / "phase1_market_overview" / "ledger_coverage_by_year.csv"
e = get_engine()
q = lambda s: pd.read_sql(s, e)
led = set(q("SELECT DISTINCT loanfile_id FROM dbo.Loan_Monthly_Activity").loanfile_id.astype(float))
ci = set(q("SELECT DISTINCT CAST(LOANFILE_ID AS numeric(38,0)) i FROM dbo.Loan_Contract_Info").i.astype(float))
rows = []
for y in range(1400, 1405):
    for mth in range(1, 13):
        ym = y * 100 + mth
        d = q(f"SELECT loanfile_id, MAX(Total_Remain) bal FROM dbo.Loan_Remain WHERE Transaction_Date BETWEEN {ym*100+1} AND {ym*100+31} GROUP BY loanfile_id")
        d["loanfile_id"] = d.loanfile_id.astype(float)
        rows.append(dict(year=y, ym=ym, total=d.bal.sum() / 1e13, ledger=d[d.loanfile_id.isin(led)].bal.sum() / 1e13, contract=d[d.loanfile_id.isin(ci)].bal.sum() / 1e13))
    print(y, flush=True)
r = pd.DataFrame(rows)
r.to_csv(OUT.with_name("ledger_coverage_monthly.csv"), index=False)
g = r.groupby("year")[["total", "ledger", "contract"]].mean()
g["ledger_share"] = g.ledger / g.total
g.reset_index().to_csv(OUT, index=False)
print(g.round(3))
