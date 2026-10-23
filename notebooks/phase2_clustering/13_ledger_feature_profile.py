"""فاز ۲ - الف-۳: پروفایل ویژگی‌های رفتار بازپرداخت از دفتر اقساط (بدون DB)."""
from pathlib import Path
import numpy as np, pandas as pd
D = Path(__file__).resolve().parents[2] / "data" / "processed" / "phase2_clustering"
lg = pd.read_pickle(D / "customer_month_ledger.pkl"); lg["cid"] = lg.cid.astype("float64").astype("int64")
lm = pd.read_pickle(D / "customer_month_loan.pkl")
log = []
def p(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); log.append(s)
lg = lg[(lg.due_ym >= 140001) & (lg.due_ym <= 140412)]
p("ledger customer-month rows (due 1400-1404)", len(lg), "primary borrowers", lg.cid.nunique(), " installments", int(lg.n_inst.sum()))
p("share installments paid %.4f ; unpaid (due in window) %.4f" % (lg.n_paid.sum() / lg.n_inst.sum(), lg.n_unpaid.sum() / lg.n_inst.sum()))
p("of paid: late>0d %.4f late>30d %.4f late>90d %.4f" % (lg.n_late.sum() / lg.n_paid.sum(), lg.n_late30.sum() / lg.n_paid.sum(), lg.n_late90.sum() / lg.n_paid.sum()))
p("status counts (installment rows): moaavagh", int(lg.n_moaavagh.sum()), " mashkoo", int(lg.n_mashkoo.sum()), " sar resid ghozashte", int(lg.n_sarresid_past.sum()))
p("max_dpd describe:", lg.max_dpd.describe(percentiles=[.5, .9, .99]).round(0).to_dict(), " negative max_dpd (paid before due) share %.3f" % (lg.max_dpd < 0).mean())
lg["y"] = lg.due_ym // 100
g = lg.groupby("y").agg(cust=("cid", "nunique"), inst=("n_inst", "sum"), paid=("n_paid", "sum"), late30=("n_late30", "sum"), unpaid=("n_unpaid", "sum"))
g["late30_rate"] = g.late30 / g.paid; g["unpaid_rate"] = g.unpaid / g.inst; p(g.round(4).to_string()); g.to_csv(D / "ledger_by_year.csv")
# پوشش نسبت به گیرندگان اصلی دارای مانده در 12/1404
l12 = lm[(lm.ym == 140412) & (lm.bal_primary > 0)]
led1404 = set(lg[lg.y == 1404].cid)
p("primary borrowers with balance 12/1404:", len(l12), " having ledger rows with due date in 1404:", len(set(l12.customer_id) & led1404), "share %.3f" % (len(set(l12.customer_id) & led1404) / len(l12)))
bal = l12.set_index("customer_id").bal_primary
cov = bal[bal.index.isin(led1404)].sum() / bal.sum(); p("balance share of those:", round(cov, 3))
# مشتریان با تأخیر مکرر
a = lg[lg.y == 1404].groupby("cid").agg(inst=("n_inst", "sum"), l30=("n_late30", "sum"), un=("n_unpaid", "sum"))
p("1404 borrowers: with any >30d late %.3f ; with >=3 late30 installments %.3f ; with any unpaid-due %.3f" % ((a.l30 > 0).mean(), (a.l30 >= 3).mean(), (a.un > 0).mean()))
(D / "ledger_feature_profile.txt").write_text("\n".join(log), encoding="utf-8")
