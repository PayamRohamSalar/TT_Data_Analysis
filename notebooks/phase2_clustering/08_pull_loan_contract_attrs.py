"""فاز ۲ - الف-۳: صفات قرارداد (نوع، نرخ، مبلغ، مدت، شعبه) و تصویر پایان ۱۲/۱۴۰۴ و ۱۲/۱۴۰۳ Loan_Remain (با بخش اقتصادی) برای تحلیل آفلاین. فقط خواندن؛ یک Engine."""
from pathlib import Path
import pandas as pd
from tt_bank.db.connection import get_engine
OUT = Path(__file__).resolve().parents[2] / "data" / "processed" / "phase2_clustering"
e = get_engine(); q = lambda s: pd.read_sql(s, e)
c = q("""SELECT c.*, b.branch_code FROM dbo.vw_Loan_Contract_Dedup c LEFT JOIN dbo.vw_Loan_Branch_Map b ON b.loanfile_id = c.loanfile_id""")
c.to_pickle(OUT / "loan_contract_attrs.pkl"); print("contracts", len(c), flush=True)
for ym in (140412, 140312, 140012):
    r = q(f"""SELECT loanfile_id, customer_id, MAX(LTRIM(RTRIM(REPLACE(ECO_SEC,CHAR(34),'')))) eco, MAX(Total_Remain) tot, MAX(MANDE_JARI) jari
              FROM dbo.Loan_Remain WHERE Transaction_Date BETWEEN {ym*100+1} AND {ym*100+31} GROUP BY loanfile_id, customer_id""")
    r.to_pickle(OUT / f"loan_remain_{ym}.pkl"); print(ym, len(r), flush=True)
lg = q("SELECT CAST(ID AS bigint) c FROM dbo.Loan_Grant_Customer"); lg.to_pickle(OUT / "loan_grant_customer.pkl")
print("done")
