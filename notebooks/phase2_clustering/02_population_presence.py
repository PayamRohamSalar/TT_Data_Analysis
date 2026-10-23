"""فاز ۲ - الف-۲: جمعیت، حضور پیوسته، ورود و خروج، توزیع ویژگی‌های سپرده (فقط از pickle؛ بدون DB)."""
from pathlib import Path
import numpy as np, pandas as pd
D = Path(__file__).resolve().parents[2] / "data" / "processed" / "phase2_clustering"
cm = pd.read_pickle(D / "customer_month_deposit.pkl")
log = []
def p(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); log.append(s)
cm["has_turn"] = (cm.crn + cm.dbn) > 0
cm["has_bal"] = cm.bal > 0
p("rows", len(cm), "customers", cm.customer_id.nunique())
dup = pd.read_csv(D / "dma_duplicate_check.csv")
p("raw rows", dup.raw_rows.sum(), "unique account-month rows", dup.unique_account_rows.sum(), "dup share %.4f" % (1 - dup.unique_account_rows.sum() / dup.raw_rows.sum()))
# سالانه
cm["y"] = cm.ym // 100
rows = []
for y, g in cm.groupby("y"):
    rows.append(dict(year=y, customers_any_row=g.customer_id.nunique(),
                     customers_turnover=g[g.has_turn].customer_id.nunique(),
                     customers_balpos=g[g.has_bal].customer_id.nunique()))
yr = pd.DataFrame(rows); yr.to_csv(D / "population_by_year.csv", index=False); p(yr.to_string())
# حضور در ۶۰ ماه
w = cm[(cm.ym >= 140001) & (cm.ym <= 140412)]
for ym0, ym1, name in [(140001, 140412, "60m"), (139901, 140412, "72m")]:
    w = cm[(cm.ym >= ym0) & (cm.ym <= ym1)]
    N = 60 if name == "60m" else 72
    g = w.groupby("customer_id").agg(n_rows=("ym", "nunique"), first=("ym", "min"), last=("ym", "max"),
                                     n_turn=("has_turn", "sum"), n_bal=("has_bal", "sum"))
    p(f"--- window {name}: customers with >=1 row {len(g)}")
    p("present all", N, "months (row exists):", int((g.n_rows == N).sum()))
    p("balance>0 all months:", int((g.n_bal == N).sum()), " turnover in all months:", int((g.n_turn == N).sum()))
    for k in [12, 24, 36, 48]:
        p(f"  months with turnover >= {k}: {(g.n_turn >= k).sum()}   with balance>0 >= {k}: {(g.n_bal >= k).sum()}")
    q = g.n_turn.describe(percentiles=[.05, .25, .5, .75, .95]); p("  n_turn dist", q.round(1).to_dict())
    g.to_csv(D / f"presence_{name}.csv")
    ent = g["first"].value_counts().sort_index(); ext = g["last"].value_counts().sort_index()
    ent.to_csv(D / f"entry_first_month_{name}.csv"); ext.to_csv(D / f"exit_last_month_{name}.csv")
    if name == "60m":
        p("entered after 140001:", int((g["first"] > 140001).sum()), " last row before 140412:", int((g["last"] < 140412).sum()))
        # آخرین ماه با گردش
        lt = w[w.has_turn].groupby("customer_id").ym.max()
        p("last turnover month before 140407 (dormant at end):", int((lt < 140407).sum()), "never turnover:", int(len(g) - len(lt)))
# توزیع ویژگی‌ها در ۱۴۰۴/۱۲
d = cm[cm.ym == 140412]
for c in ["n_accounts", "bal", "cr", "db", "crn", "dbn"]:
    s = d[c].describe(percentiles=[.01, .05, .25, .5, .75, .95, .99]); p("140412", c, s.round(0).to_dict())
p("140412 negative balance customers", int((d.bal < 0).sum()), " zero balance", int((d.bal == 0).sum()), " neg_acc>0", int((d.neg_acc > 0).sum()))
allneg = cm[cm.bal < 0]; p("customer-months with negative balance (all)", len(allneg), "share %.5f" % (len(allneg) / len(cm)))
p("customer-months credit<0:", int((cm.cr < 0).sum()), " debit<0:", int((cm.db < 0).sum()), " counts<0:", int(((cm.crn < 0) | (cm.dbn < 0)).sum()))
p("turnover>0 but balance==0:", int(((cm.has_turn) & (cm.bal == 0)).sum()), " bal>0 no turnover:", int(((~cm.has_turn) & (cm.bal > 0)).sum()))
# عدم‌تقارن گردش: بستانکار و بدهکار
t = cm[cm.has_turn]; p("turnover months: share with credit==0:", round((t.cr == 0).mean(), 4), "debit==0:", round((t.db == 0).mean(), 4))
# ماه‌به‌ماه تعداد مشتری
mm = cm.groupby("ym").agg(customers=("customer_id", "nunique"), turn=("has_turn", "sum"), bal=("bal", "sum")); mm.to_csv(D / "customers_by_month.csv")
(D / "population_deposit_probe.txt").write_text("\n".join(log), encoding="utf-8")
