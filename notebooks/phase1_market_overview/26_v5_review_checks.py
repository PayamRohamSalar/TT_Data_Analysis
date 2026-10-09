"""بازبینی ادعاهای داوران ویرایش پنجم (فقط خواندن؛ DB). خروجی: v5_review_checks.txt   (فقط یک Engine؛ python -u مستقیم)"""
from pathlib import Path
import pandas as pd
from tt_bank.db.connection import get_engine

OUT = Path(__file__).resolve().parents[2] / "data" / "processed" / "phase1_market_overview" / "v5_review_checks.txt"
log = []
def p(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); log.append(s)
e = get_engine(); q = lambda s: pd.read_sql(s, e)
G = set(q("SELECT DISTINCT CAST(ID AS bigint) c FROM dbo.Loan_Grant_Customer").c)
P = set(q("SELECT DISTINCT CAST(customer_id AS bigint) c FROM dbo.Loan_Remain WHERE Transaction_Date BETWEEN 14041201 AND 14041231").c)
oa = q("SELECT DISTINCT CAST(MAIN_CUSTOMER_ID AS bigint) c FROM dbo.Deposit_Accoutnt_Info")
DEP = set(oa.c)
dm12 = q("SELECT CAST(customer_id AS bigint) c, SUM(avr_total_amount_eq) b FROM dbo.Deposit_Monthly_Activity WHERE year_mount=140412 GROUP BY customer_id")
big = dm12[dm12.b >= 1e10]
p("depositor set (Account_Info)", len(DEP), " big(>1bn) total", len(big), " big in DEP", big.c.isin(DEP).sum(), " big not in DEP", (~big.c.isin(DEP)).sum())
p("big in DEP & not G:", len(set(big.c) & DEP - G), " of which parties(P):", len(set(big.c) & DEP - G & P), " neither:", len(set(big.c) & DEP - G - P))
only = DEP - G
p("depositors not in G:", len(only), " of which loan parties (guarantor/partner):", len(only & P), " no contract link:", len(only - P))
p("G in DEP:", len(G & DEP), "G not in DEP:", len(G - DEP))
# حساب‌های بدون رکورد مشخصات
a_dm = q("SELECT DISTINCT deposit_id FROM dbo.Deposit_Monthly_Activity WHERE year_mount=140412")
a_info = q("SELECT DEPOSIT_ID, MAX(MAINTYPE_NAME) t FROM dbo.Deposit_Accoutnt_Info GROUP BY DEPOSIT_ID")
a_info["DEPOSIT_ID"] = a_info.DEPOSIT_ID.astype(float); a_dm["deposit_id"] = a_dm.deposit_id.astype(float)
m = a_dm.merge(a_info, left_on="deposit_id", right_on="DEPOSIT_ID", how="left")
p("accounts 12/1404 distinct", len(a_dm), " without info record", int(m.DEPOSIT_ID.isna().sum()), " with info but empty type", int((m.DEPOSIT_ID.notna() & m.t.isna()).sum()))
OUT.write_text("\n".join(log), encoding="utf-8")
