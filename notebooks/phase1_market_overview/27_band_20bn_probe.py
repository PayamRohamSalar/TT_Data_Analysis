"""بررسی علت ۴۰۱ در برابر ۲۶۲ در طبقه‌ی بیش از ۲۰ میلیارد تومان (کامنت مشاور). فقط خواندن؛ یک Engine."""
from pathlib import Path
import numpy as np, pandas as pd
from tt_bank.db.connection import get_engine
OUT = Path(__file__).resolve().parents[2] / "data" / "processed" / "phase1_market_overview" / "band_20bn_probe.txt"
log=[]
def p(*a):
    s=" ".join(str(x) for x in a); print(s,flush=True); log.append(s)
e=get_engine()
info=pd.read_sql("SELECT DISTINCT CAST(LOANFILE_ID AS numeric(38,0)) AS loanfile_id, CAST(LTRIM(RTRIM(MAIN_CUSTOMER_ID)) AS numeric(38,0)) AS main_id FROM dbo.Loan_Contract_Info WHERE ISNUMERIC(LTRIM(RTRIM(MAIN_CUSTOMER_ID)))=1",e).drop_duplicates("loanfile_id")
G=set(pd.read_sql("SELECT DISTINCT ID c FROM dbo.Loan_Grant_Customer",e).c)
fr=[]
for ym in range(140401,140413):
    df=pd.read_sql(f"SELECT customer_id, loanfile_id, MAX(Total_Remain) bal FROM dbo.Loan_Remain WHERE Transaction_Date BETWEEN {ym*100+1} AND {ym*100+31} GROUP BY customer_id, loanfile_id",e)
    c=df.groupby("loanfile_id").agg(bal=("bal","max"),n=("customer_id","nunique"),fp=("customer_id","min")).reset_index().merge(info,on="loanfile_id",how="left")
    c["owner"]=c.main_id; s=c.owner.isna()&(c.n==1); c.loc[s,"owner"]=c.loc[s,"fp"]
    c["ym"]=ym; fr.append(c.dropna(subset=["owner"])[["owner","ym","bal"]]); print(ym,flush=True)
a=pd.concat(fr); M=a.groupby(["owner","ym"]).bal.sum().unstack(fill_value=0)
T=2e11
def cnt(s,lab): p(lab,"all owners:",int((s>=T).sum())," in primary list:",int((s[s.index.isin(G)]>=T).sum()))
cnt(M[[m for m in M.columns if m<=140409]].sum(axis=1)/9,"avg 01-09 (report basis)")
cnt(M[140409],"point 09/1404"); cnt(M[140412],"point 12/1404")
cnt(M[[m for m in M.columns if m<=140409]].max(axis=1),"max 01-09")
nz=M[[m for m in M.columns if m<=140409]].replace(0,np.nan).mean(axis=1); cnt(nz.fillna(0),"avg of nonzero months 01-09")
# بدون قراردادهای اعتبار اسنادی؟ شناسه‌ی نوع در Loan_Remain نیست؛ فقط ثبت
M9=M[140409]; top=M9[M9>=T].sort_values(ascending=False)
p("owners >=200bn rial at 09/1404:",len(top)," top5 balances (rial):",list(top.head(5).round(0)))
p("share of those that are in primary list:", float(top.index.isin(G).mean()))
OUT.write_text("\n".join(log),encoding="utf-8")
