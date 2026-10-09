"""بازبینی ادعاهای داوران نسخه‌ی v4 با داده (فقط خواندن؛ نیازمند DB). خروجی: data/processed/phase1_market_overview/v4_review_checks.txt
فقط یک Engine (SQL Server تک‌کاربره)؛ اجرا: python -u مستقیم."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from tt_bank.db.connection import get_engine

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "processed" / "phase1_market_overview" / "v4_review_checks.txt"
log = []


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    log.append(s)


e = get_engine()
q = lambda sql: pd.read_sql(sql, e)

# ---- ۱) جمعیت‌ها: Venn
D = set(q("SELECT DISTINCT CUSTOMER_ID c FROM dbo.Deposit_Customer").c)
G = set(q("SELECT DISTINCT ID c FROM dbo.Loan_Grant_Customer").c)
R = set(q("SELECT DISTINCT ID c FROM dbo.Loan_Remain_Customer").c)
par = q("SELECT DISTINCT customer_id c FROM dbo.Loan_Remain WHERE Transaction_Date BETWEEN 14041201 AND 14041231")
P = set(par.c)
dep = q("SELECT DISTINCT customer_id c FROM dbo.Deposit_Monthly_Activity")
DM = set(dep.c)
p("sizes D", len(D), "G", len(G), "R", len(R), "parties12/1404", len(P), "DM(all months)", len(DM))
p("DM∩D", len(DM & D), "DM∩G", len(DM & G), "DM∩R", len(DM & R), "DM∩P", len(DM & P), "DM−(D∪R∪G)", len(DM - D - R - G), "DM−(D∪P)", len(DM - D - P))
p("D−DM", len(D - DM), "union(D,R,G)", len(D | R | G))

# ---- ۲) کوهورت ۱۴۰۴: تاریخ نخستین حساب
oa = q("SELECT MAIN_CUSTOMER_ID c, MIN(OPEN_DATE) mn FROM dbo.Deposit_Accoutnt_Info GROUP BY MAIN_CUSTOMER_ID")
oa["yr"] = oa.mn.astype(str).str[:4]
c04 = set(oa[oa.yr == "1404"].c)
p("cohort1404 size (first-account year 1404, in DM):", len(c04 & DM))
p("  in D:", len(c04 & DM & D), " in R:", len(c04 & DM & R), " in G:", len(c04 & DM & G), " in parties:", len(c04 & DM & P), " in none of D,R,G:", len((c04 & DM) - D - R - G))
oa_early = oa[(oa.yr >= "1380") & (oa.yr < "1404")]
p("cohort yr dist (in DM) top:", oa[oa.c.isin(DM)].yr.value_counts().sort_index().tail(8).to_dict())

# ---- ۳) سال اعطا
gy = q("SELECT LEFT(GRANT_DATE,4) y, COUNT(*) n FROM dbo.Loan_Contract_Info GROUP BY LEFT(GRANT_DATE,4) ORDER BY 1")
p("grant years:", dict(zip(gy.y, gy.n)))

# ---- ۴) شمار حساب‌ها
a1 = q("SELECT COUNT(DISTINCT deposit_id) n FROM dbo.Deposit_Monthly_Activity WHERE year_mount=140412").n[0]
a2 = q("SELECT COUNT(DISTINCT deposit_id) n FROM dbo.Deposit_Monthly_Activity").n[0]
a3 = q("SELECT COUNT(DISTINCT DEPOSIT_ID) n FROM dbo.Deposit_Accoutnt_Info").n[0]
p("accounts distinct: DMA 12/1404", a1, "DMA all", a2, "Account_Info", a3)

# ---- ۵) قرارداد: وزن نرخ، فروش اقساطی، طرفین
rem = q("""SELECT loanfile_id, MAX(Total_Remain) bal, MAX(Overusance_Remain)+MAX(Postponed_Remain)+MAX(Doubtful_Remain) npl,
           COUNT(DISTINCT customer_id) parties, MAX(ECO_SEC) eco
           FROM dbo.Loan_Remain WHERE Transaction_Date BETWEEN 14041201 AND 14041231 GROUP BY loanfile_id""")
ci = q("""SELECT CAST(LOANFILE_ID AS numeric(38,0)) loanfile_id, MAX(LOAN_TYPE_DESCRIPTION) typ, MAX(GRANT_AMOUNT) grant_amt, MAX(USED_COST) used,
          MAX(APPROVED_AMOUNT) appr, MAX(LOAN_INTEREST_RATE) r1, MAX(LOAN_PREFERED_RATE) r2, MAX(GRANT_DATE) gd
          FROM dbo.Loan_Contract_Info GROUP BY LOANFILE_ID""")
rem["loanfile_id"] = rem.loanfile_id.astype("float64")
ci["loanfile_id"] = ci.loanfile_id.astype("float64")
m = rem.merge(ci, on="loanfile_id", how="left")
m["known"] = m.typ.notna()
tot = m.bal.sum()
p("total bal 12/1404 (toman 1e13):", tot / 1e13, "known share", m[m.known].bal.sum() / tot)
k = m[m.known & (m.bal > 0)].copy()
k["rate"] = pd.to_numeric(k.r1, errors="coerce").fillna(0) + pd.to_numeric(k.r2, errors="coerce").fillna(0)
p("balance-weighted contractual rate (known, bal>0):", (k.rate * k.bal).sum() / k.bal.sum())
kg = ci.copy(); kg["rate"] = pd.to_numeric(kg.r1, errors="coerce").fillna(0) + pd.to_numeric(kg.r2, errors="coerce").fillna(0)
kg["grant_amt"] = pd.to_numeric(kg.grant_amt, errors="coerce")
p("grant-weighted rate all contracts:", (kg.rate * kg.grant_amt).sum() / kg.grant_amt.sum())
p("grant-weighted rate contracts with balance>0 at 12/1404:", (k.rate * pd.to_numeric(k.grant_amt, errors='coerce')).sum() / pd.to_numeric(k.grant_amt, errors='coerce').sum())
# فروش اقساطی
inst = m[m.known & m.typ.astype(str).str.contains("اقساط|اقساطي")]
p("installment sale: n", len(inst), "balance(1e13)", inst.bal.sum() / 1e13, "grant", pd.to_numeric(inst.grant_amt, errors="coerce").sum() / 1e13,
  "used_cost", pd.to_numeric(inst.used, errors="coerce").sum() / 1e13, "approved", pd.to_numeric(inst.appr, errors="coerce").sum() / 1e13)
# طرفین
m["bucket"] = pd.cut(m.parties, [0, 1, 3, 6, 10, 1e9], labels=["1", "2-3", "4-6", "7-10", "11+"])
m["lc"] = m.eco.astype(str).str.contains("اعتباراسنادی")
for nm, sub in (("all", m), ("ex-LC", m[~m.lc]), ("known ex-LC", m[m.known & ~m.lc]), ("unknown ex-LC", m[~m.known & ~m.lc]), ("LC", m[m.lc])):
    g = sub.groupby("bucket", observed=True).agg(n=("bal", "size"), bal=("bal", "sum"), npl=("npl", "sum"))
    g["ratio"] = 100 * g.npl / g.bal
    p("parties bucket", nm, {str(i): (int(r.n), round(r.bal / 1e13, 2), round(r.ratio, 2)) for i, r in g.iterrows()})
p("LC contracts: known share", m[m.lc].known.mean(), "parties dist", m[m.lc].parties.value_counts().head(5).to_dict())

# ---- ۶) ۸۴ مشتری
dm12 = q("SELECT customer_id c, SUM(avr_total_amount_eq) b FROM dbo.Deposit_Monthly_Activity WHERE year_mount=140412 GROUP BY customer_id")
big = dm12[dm12.b >= 1e10]
p("deposit >1bn toman (>=1e10 rial) customers:", len(big), " in G:", big.c.isin(G).sum(), " not in G:", (~big.c.isin(G)).sum(),
  " in DM:", big.c.isin(DM).sum(), " in D:", big.c.isin(D).sum(), " in parties:", big.c.isin(P).sum())
OUT.write_text("\n".join(log), encoding="utf-8")
