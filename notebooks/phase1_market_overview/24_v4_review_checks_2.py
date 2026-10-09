"""بازبینی تکمیلی (فقط خواندن؛ نیازمند DB): کوهورت ۱۴۰۴، قدمت قراردادهای بدون رکورد، نرخ قراردادی وزن‌دهی‌شده با مانده، پوشش دفتر اقساط.
خروجی: data/processed/phase1_market_overview/v4_review_checks_2.txt و rate_by_type_balance_weighted.csv
فقط یک Engine؛ اجرا: python -u مستقیم."""
from pathlib import Path

import numpy as np
import pandas as pd

from tt_bank.db.connection import get_engine

ROOT = Path(__file__).resolve().parents[2]
OUTD = ROOT / "data" / "processed" / "phase1_market_overview"
log = []


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    log.append(s)


e = get_engine()
q = lambda sql: pd.read_sql(sql, e)

# --- کوهورت ۱۴۰۴
oa = q("SELECT CAST(MAIN_CUSTOMER_ID AS bigint) c, MIN(OPEN_DATE) mn FROM dbo.Deposit_Accoutnt_Info GROUP BY MAIN_CUSTOMER_ID")
oa["yr"] = oa.mn.astype(str).str[:4]
D = set(q("SELECT DISTINCT CAST(CUSTOMER_ID AS bigint) c FROM dbo.Deposit_Customer").c)
G = set(q("SELECT DISTINCT CAST(ID AS bigint) c FROM dbo.Loan_Grant_Customer").c)
P = set(q("SELECT DISTINCT CAST(customer_id AS bigint) c FROM dbo.Loan_Remain WHERE Transaction_Date BETWEEN 14041201 AND 14041231").c)
DM = set(q("SELECT DISTINCT CAST(customer_id AS bigint) c FROM dbo.Deposit_Monthly_Activity").c)
c04 = set(oa[oa.yr == "1404"].c) & DM
p("cohort1404:", len(c04), "in D", len(c04 & D), "in G", len(c04 & G), "in parties", len(c04 & P), "in P but not D", len((c04 & P) - D), "in neither D nor P", len(c04 - D - P))
y = oa[oa.c.isin(DM)].yr.value_counts().sort_index()
p("first-account year dist (in DM):", y.tail(8).to_dict(), "oa rows", len(oa), "DM covered by oa:", len(DM & set(oa.c)))
d_only = oa[oa.c.isin(D)]
p("deposit-stratum customers with first-account year 1404:", int((d_only.yr == "1404").sum()), "of", len(d_only), " year>=1403:", int((d_only.yr >= "1403").sum()))

# --- قدمت قراردادهای بدون رکورد
first = q("SELECT loanfile_id, MIN(Transaction_Date) mn FROM dbo.Loan_Remain GROUP BY loanfile_id")
ci_ids = set(q("SELECT DISTINCT CAST(LOANFILE_ID AS numeric(38,0)) i FROM dbo.Loan_Contract_Info").i.astype(float))
first["known"] = first.loanfile_id.astype(float).isin(ci_ids)
last = q("SELECT loanfile_id, MAX(Total_Remain) bal FROM dbo.Loan_Remain WHERE Transaction_Date BETWEEN 14041201 AND 14041231 GROUP BY loanfile_id")
f2 = first.merge(last, on="loanfile_id")
f2["early"] = f2.mn.astype("int64") < 13990201
for k, g in f2.groupby("known"):
    p("known" if k else "unknown", "contracts", len(g), "first-seen before 1399/02 (data start):", round(100 * g.early.mean(), 1), "% ; balance share early:", round(100 * g[g.early].bal.sum() / g.bal.sum(), 1))

# --- نرخ قراردادی وزن‌دهی‌شده با مانده به تفکیک نوع
ci = q("""SELECT CAST(LOANFILE_ID AS numeric(38,0)) loanfile_id, MAX(LOAN_TYPE_DESCRIPTION) typ, MAX(LOAN_INTEREST_RATE) r1, MAX(LOAN_PREFERED_RATE) r2
          FROM dbo.Loan_Contract_Info GROUP BY LOANFILE_ID""")
ci["loanfile_id"] = ci.loanfile_id.astype(float)
last["loanfile_id"] = last.loanfile_id.astype(float)
m = last.merge(ci, on="loanfile_id", how="inner")
m = m[m.bal > 0].copy()
t = m.typ.astype(str)
m["grp"] = np.select([t.str.contains("قرض الحسنه"), t.str.contains("مرابحه"), t.str.contains("مشارکت مدني"), t.str.contains("فروش اقساطي"),
                      t.str.contains("جعاله"), t.str.contains("مضاربه")],
                     ["قرض‌الحسنه", "مرابحه", "مشارکت مدنی", "فروش اقساطی", "جعاله", "مضاربه"], "سایر")
m["rate"] = pd.to_numeric(m.r1, errors="coerce").fillna(0) + pd.to_numeric(m.r2, errors="coerce").fillna(0)
g = m.groupby("grp").apply(lambda d: pd.Series({"balance": d.bal.sum() / 1e13, "rate_bal_weighted": (d.rate * d.bal).sum() / d.bal.sum()}))
g["share"] = 100 * g.balance / g.balance.sum()
tot = (m.rate * m.bal).sum() / m.bal.sum()
p("balance-weighted by type:\n" + g.round(2).to_string(), "\ntotal", round(tot, 3))
ex = m[m.grp != "قرض‌الحسنه"]
p("ex-qarz total:", round((ex.rate * ex.bal).sum() / ex.bal.sum(), 3))
g.reset_index().to_csv(OUTD / "rate_by_type_balance_weighted.csv", index=False, encoding="utf-8-sig")

# --- پوشش دفتر اقساط روی میانگین مانده‌ی ۱۴۰۴
led = set(q("SELECT DISTINCT loanfile_id FROM dbo.Loan_Monthly_Activity").loanfile_id.astype(float))
rows = []
for ym in range(140401, 140413):
    d = q(f"SELECT loanfile_id, MAX(Total_Remain) bal FROM dbo.Loan_Remain WHERE Transaction_Date BETWEEN {ym*100+1} AND {ym*100+31} GROUP BY loanfile_id")
    d["loanfile_id"] = d.loanfile_id.astype(float)
    tot_b = d.bal.sum()
    rows.append(dict(ym=ym, total=tot_b / 1e13, ledger=d[d.loanfile_id.isin(led)].bal.sum() / 1e13, contract=d[d.loanfile_id.isin(ci_ids)].bal.sum() / 1e13,
                     both=d[d.loanfile_id.isin(led & ci_ids)].bal.sum() / 1e13))
r = pd.DataFrame(rows)
p("monthly balances (1e13):\n" + r.round(2).to_string())
p("avg 1404: total", round(r.total.mean(), 2), "ledger", round(r.ledger.mean(), 2), "contract", round(r.contract.mean(), 2),
  "ledger share", round(r.ledger.mean() / r.total.mean(), 4), "contract share", round(r.contract.mean() / r.total.mean(), 4))
(OUTD / "v4_review_checks_2.txt").write_text("\n".join(log), encoding="utf-8")
