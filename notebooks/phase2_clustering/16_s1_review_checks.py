"""فاز ۲ - بازبینی S1 (بدون DB): یکتایی کلید، حساسیت آستانه‌ی نهادی، ترکیب گروه بی‌فعالیت، پوشش وام بدون سپرده."""
from pathlib import Path
import numpy as np, pandas as pd
D = Path(__file__).resolve().parents[2] / "data" / "processed" / "phase2_clustering"
log = []
def p(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); log.append(s)
pan = pd.read_pickle(D / "panel_customer_year.pkl")
p("rows", len(pan), "unique (customer,year)", len(pan.drop_duplicates(["customer_id", "y"])))
p("null counts:", pan[["months", "turn_months", "bal_mean", "bal_dec"]].isna().sum().to_dict())
p("customers without Dec row (bal_dec NaN) by year:", pan[pan.bal_dec.isna()].groupby("y").size().to_dict())
# حساسیت آستانه‌ی نهادی (1404): تعداد و سهم مانده
a = pan[pan.y == 1404]
for t in (20, 30, 50, 100, 200, 500):
    s = a[a.nacc_max >= t]
    p(f"1404 nacc_max>={t}: customers {len(s)} share of customers {len(s)/len(a):.4f} share of avg balance {s.bal_mean.sum()/a.bal_mean.sum():.3f}")
# رفتار حساب‌ها برای نهادی‌های کاندیدا: آیا فقط در یک ماه جهش دارند؟
cm = pd.read_pickle(D / "customer_month_deposit.pkl")
big = set(a[a.nacc_max >= 100].customer_id)
s = cm[(cm.ym // 100 == 1404) & cm.customer_id.isin(big)]
m = s.groupby("customer_id").agg(nmin=("n_accounts", "min"), nmed=("n_accounts", "median"), nmax=("n_accounts", "max"), months=("ym", "nunique"))
p("institutional candidates 1404: n", len(m), " min-accounts>=50 in all months share %.3f" % (m.nmin >= 50).mean(), " median accounts p50 %.0f p10 %.0f" % (m.nmed.median(), m.nmed.quantile(.1)))
p("   those with nmax>=100 but nmed<100:", int(((m.nmax >= 100) & (m.nmed < 100)).sum()))
# بی‌فعالیت: ترکیب علت
b = a[a.category == "idle_token"]
p("idle_token 1404:", len(b), " turn<3 only:", int(((b.turn_months < 3) & (b.bal_max >= 5e6)).sum()), " bal_max<5m only:", int(((b.turn_months >= 3) & (b.bal_max < 5e6)).sum()),
  " both:", int(((b.turn_months < 3) & (b.bal_max < 5e6)).sum()))
p("   idle with loan (party or primary):", int((b.bal_party > 0).sum()), " primary:", int((b.bal_primary > 0).sum()))
# هم‌پوشانی گروه با وام
for cat in ["model", "idle_token", "newcomer", "institutional_candidate"]:
    c = a[a.category == cat]; p(f"1404 {cat}: n {len(c)} primary-record share {(c.bal_primary>0).mean():.3f} party>0 share {(c.bal_party>0).mean():.3f}")
# وام‌داران بدون ردیف سپرده در پانل (از جدول وام)
lm = pd.read_pickle(D / "customer_month_loan.pkl")
l = lm[(lm.ym % 100 == 12) & (lm.bal_party > 0)]
l["y"] = l.ym // 100
for y, g in l.groupby("y"):
    inp = set(pan[pan.y == y].customer_id)
    p(f"{y}: loan parties at Dec {len(g)}; not in deposit panel that year: {int((~g.customer_id.isin(inp)).sum())}")
(D / "s1_review_checks.txt").write_text("\n".join(log), encoding="utf-8")
