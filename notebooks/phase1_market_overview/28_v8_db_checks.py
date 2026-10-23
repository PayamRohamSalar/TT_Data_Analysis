"""بازبینی ارقام افزوده‌شده در v8 (فقط خواندن؛ یک Engine). خروجی: v8_db_checks.txt"""
from pathlib import Path
import numpy as np, pandas as pd
from tt_bank.db.connection import get_engine
OUT = Path(__file__).resolve().parents[2] / "data" / "processed" / "phase1_market_overview" / "v8_db_checks.txt"
log=[]
def p(*a):
    s=" ".join(str(x) for x in a); print(s,flush=True); log.append(s)
e=get_engine(); q=lambda s: pd.read_sql(s,e)
S=set(q("SELECT DISTINCT CAST(CUSTOMER_ID AS bigint) c FROM dbo.Deposit_Customer").c)
P=set(q("SELECT DISTINCT CAST(customer_id AS bigint) c FROM dbo.Loan_Remain WHERE Transaction_Date BETWEEN 14041201 AND 14041231").c)
G=set(q("SELECT DISTINCT CAST(ID AS bigint) c FROM dbo.Loan_Grant_Customer").c)
DEP=set(q("SELECT DISTINCT CAST(LTRIM(RTRIM(MAIN_CUSTOMER_ID)) AS numeric(38,0)) c FROM dbo.Deposit_Accoutnt_Info").c.astype('int64'))
p("stratum",len(S),"loan parties",len(P),"overlap",len(S&P))
p("parties not in stratum",len(P-S),"of which with deposit account",len((P-S)&DEP),"without",len((P-S)-DEP))
p("stratum in DEP",len(S&DEP),"DEP total",len(DEP),"DEP == S | (P&DEP)?",DEP==(S|(P&DEP)), len(DEP-(S|P)))
p("grant list",len(G),"in DEP",len(G&DEP),"not in DEP",len(G-DEP),"union DEP|G",len(DEP|G))
b=q("SELECT customer_id, SUM(avr_total_amount_eq) b FROM dbo.Deposit_Monthly_Activity WHERE year_mount=140412 GROUP BY customer_id")
b=b[b.b>0].sort_values("b",ascending=False)
n=len(b); k=int(np.ceil(n*0.01)); top=b.b.head(k).sum()/b.b.sum()
p("depositors with positive balance 12/1404",n,"top1% count",k,"share",round(100*top,2))
OUT.write_text("\n".join(log),encoding="utf-8")
