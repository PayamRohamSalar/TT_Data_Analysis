"""فاز ۲ - الف-۲: پوشش نوع حساب در سطح مشتری (۱۲/۱۴۰۴)، مشتریان بدون رکورد حساب، تعارض گیرنده‌ی اصلی در تکرارهای قرارداد (فقط خواندن؛ یک Engine)."""
from pathlib import Path
import numpy as np, pandas as pd
from tt_bank.db.connection import get_engine
D = Path(__file__).resolve().parents[2] / "data" / "processed" / "phase2_clustering"
e = get_engine(); q = lambda s: pd.read_sql(s, e)
log = []
def p(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); log.append(s)
def save(): (D / "probe_account_types_misc.txt").write_text("\n".join(log), encoding="utf-8")
# الف) مانده‌ی هر نوع حساب هر مشتری در 140412
t = q("""SELECT d.customer_id, ISNULL(a.deposit_type, N'(بدون رکورد حساب)') typ, COUNT(*) n_acc, SUM(d.bal) bal
         FROM (SELECT customer_id, deposit_id, MAX(avr_total_amount_eq) bal FROM dbo.Deposit_Monthly_Activity WHERE year_mount=140412 GROUP BY customer_id, deposit_id) d
         LEFT JOIN dbo.vw_Deposit_Account_Dedup a ON a.deposit_id = d.deposit_id
         GROUP BY d.customer_id, ISNULL(a.deposit_type, N'(بدون رکورد حساب)')""")
t = t[t.customer_id.notna()].copy(); t["customer_id"] = t.customer_id.astype("float64").astype("int64")
t.to_pickle(D / "deposit_type_balance_140412.pkl")
tot = t.groupby("typ").agg(n_acc=("n_acc", "sum"), bal=("bal", "sum")); tot["acc_share"] = tot.n_acc / tot.n_acc.sum(); tot["bal_share"] = tot.bal / tot.bal.sum()
p("account types at 12/1404 (accounts with activity row):\n" + tot.round(4).to_string()); tot.to_csv(D / "account_type_share_140412.csv", encoding="utf-8-sig")
c = t.groupby("customer_id").apply(lambda g: pd.Series(dict(bal=g.bal.sum(), unk=g[g.typ.str.startswith("(بدون")].bal.sum(), n=g.n_acc.sum(), nunk=g[g.typ.str.startswith("(بدون")].n_acc.sum())), include_groups=False)
c["unk_share"] = c.unk / c.bal.replace(0, np.nan)
p("customers 12/1404:", len(c), " with any account lacking info:", int((c.nunk > 0).sum()), " all accounts lack info:", int((c.nunk == c.n).sum()),
  " balance-weighted unknown share among customers with balance>0: %.3f" % (c.unk.sum() / c.bal.sum()))
p("customers whose unknown share >50% of their balance:", int((c.unk_share > .5).sum()))
save()
# ب) مشتریان سپرده بدون رکورد حساب
acc = set(q("SELECT DISTINCT CAST(LTRIM(RTRIM(MAIN_CUSTOMER_ID)) AS bigint) c FROM dbo.Deposit_Accoutnt_Info WHERE ISNUMERIC(LTRIM(RTRIM(MAIN_CUSTOMER_ID)))=1").c)
cmc = set(pd.read_pickle(D / "customer_month_deposit.pkl", ).customer_id.unique())
p("customers in Deposit_Monthly_Activity (72m):", len(cmc), " not in Account_Info:", len(cmc - acc), " in Account_Info but never in DMA:", len(acc - cmc))
pd.Series(sorted(cmc - acc), name="customer_id").to_csv(D / "dma_customers_not_in_account_info.csv", index=False)
# ج) تعارض گیرنده‌ی اصلی در تکرارهای قرارداد
x = q("SELECT COUNT(*) n FROM (SELECT LOANFILE_ID FROM dbo.Loan_Contract_Info GROUP BY LOANFILE_ID HAVING COUNT(DISTINCT MAIN_CUSTOMER_ID)>1) a"); p("LOANFILE_ID with >1 distinct MAIN_CUSTOMER_ID:", int(x.n[0]))
y = q("SELECT COUNT(*) n, SUM(CASE WHEN MAIN_CUSTOMER_ID IS NULL THEN 1 ELSE 0 END) nulls FROM dbo.Loan_Contract_Info"); p("Loan_Contract_Info rows", int(y.n[0]), "null main customer", int(y.nulls[0]))
# د) مشتریان بدون حساب باز؛ وضعیت مسدودی در سطح مشتری
b = q("""SELECT COUNT(DISTINCT CAST(LTRIM(RTRIM(MAIN_CUSTOMER_ID)) AS bigint)) n FROM dbo.Deposit_Accoutnt_Info WHERE LTRIM(RTRIM(STATUS_NAME)) <> N'باز'"""); p("customers with at least one blocked/non-open account:", int(b.n[0]))
save()
