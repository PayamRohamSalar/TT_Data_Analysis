"""فاز ۲ - الف-۱/۵: اندازه‌ی پانل مشتری-سال تحت قواعد مختلف واجد شرایط‌بودن؛ سهم گروه‌های بی‌فعالیت (بدون DB)."""
from pathlib import Path
import numpy as np, pandas as pd
D = Path(__file__).resolve().parents[2] / "data" / "processed" / "phase2_clustering"
cm = pd.read_pickle(D / "customer_month_deposit.pkl"); lm = pd.read_pickle(D / "customer_month_loan.pkl")
log = []
def p(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); log.append(s)
cm["y"] = cm.ym // 100; cm["turn"] = ((cm.crn + cm.dbn) > 0).astype(np.int8)
g = cm.groupby(["customer_id", "y"]).agg(months=("ym", "nunique"), turn=("turn", "sum"), bal_mean=("bal", "mean"), bal_max=("bal", "max"), nacc=("n_accounts", "max")).reset_index()
rows = []
for y in range(1399, 1405):
    s = g[g.y == y]
    rows.append(dict(year=y, all=len(s), m12=int((s.months == 12).sum()), m6=int((s.months >= 6).sum()),
        m6_turn3=int(((s.months >= 6) & (s.turn >= 3)).sum()), m12_turn6=int(((s.months == 12) & (s.turn >= 6)).sum()),
        tiny=int((s.bal_max < 5e6).sum()), no_turn=int((s.turn == 0).sum()), inst_100acc=int((s.nacc >= 100).sum())))
t = pd.DataFrame(rows); t.to_csv(D / "panel_eligibility_by_year.csv", index=False); p(t.to_string())
p("panel customer-years 1400-1404: all", int(t[t.year >= 1400]["all"].sum()), " months>=6 & turn>=3:", int(t[t.year >= 1400].m6_turn3.sum()))
# شمار مشتریان واجد شرایط در همه ۵ سال
ok = g[(g.y >= 1400) & (g.months >= 6) & (g.turn >= 3)].groupby("customer_id").y.nunique()
p("customers eligible in k of 5 years:", ok.value_counts().sort_index().to_dict())
# تعریف فعالیت فاز ۱ در ۱۴۰۴: تازگی و ... در سطح سال ۱۴۰۴
s = g[g.y == 1404]
p("1404: bal_max<5m rial:", int((s.bal_max < 5e6).sum()), " turn==0:", int((s.turn == 0).sum()), " both-small-or-idle:", int(((s.bal_max < 5e6) | (s.turn == 0)).sum()))
# توزیع ماهیت: دهک‌های اندازه ۱۴۰۴ و سهم از مانده
s = s.sort_values("bal_mean", ascending=False); cs = s.bal_mean.cumsum() / s.bal_mean.sum()
for q in (.001, .01, .05, .10, .25, .50):
    k = int(len(s) * q); p(f"1404 top {q*100:g}% customers hold {cs.iloc[k-1]:.3f} of avg balance; threshold bal_mean {s.bal_mean.iloc[k-1]:.3g} rial")
# وام × سپرده ۱۴۰۴
lm12 = lm[lm.ym == 140412]; hasl = set(lm12[lm12.bal_primary > 0].customer_id)
s["borrower"] = s.customer_id.isin(hasl)
p("1404 balance share: borrowers %.3f of deposit avg balance; borrowers share of customers %.3f" % (s[s.borrower].bal_mean.sum() / s.bal_mean.sum(), s.borrower.mean()))
p("borrower median avg deposit balance (rial): %.3g vs non-borrower %.3g" % (s[s.borrower].bal_mean.median(), s[~s.borrower].bal_mean.median()))
# سناریوی «پایه‌ی نمونه» ورود/خروج: مشتریان با ورود پس از شروع
first = cm.groupby("customer_id").ym.min()
p("entered in 1404 (first row 1404):", int((first >= 140401).sum()), "entered 1403:", int(((first >= 140301) & (first < 140401)).sum()))
(D / "panel_eligibility.txt").write_text("\n".join(log), encoding="utf-8")
