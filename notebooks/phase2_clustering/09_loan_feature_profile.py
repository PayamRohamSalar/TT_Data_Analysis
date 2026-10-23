"""فاز ۲ - الف-۳: پروفایل ویژگی‌های تسهیلات و هم‌پوشانی با سپرده (بدون DB؛ از pickle)."""
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import skew
D = Path(__file__).resolve().parents[2] / "data" / "processed" / "phase2_clustering"
lm = pd.read_pickle(D / "customer_month_loan.pkl")
dm = pd.read_pickle(D / "customer_month_deposit.pkl")
log = []
def p(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); log.append(s)
chk = pd.read_csv(D / "loan_remain_checks.csv"); p("Loan_Remain checks (sum over 60 months): null-customer rows", int(chk.null_customer_rows.sum()),
  "negative total rows", int(chk.negative_total_rows.sum()), "components mismatch rows", int(chk.components_mismatch_rows.sum()))
p("loan customer-month rows", len(lm), "customers (party basis)", lm.customer_id.nunique())
lm["y"] = lm.ym // 100
yr = []
for y, g in lm.groupby("y"):
    de = g[g.ym == y * 100 + 12]
    yr.append(dict(year=y, party_customers_any_month=g.customer_id.nunique(), party_customers_dec=len(de),
                   primary_customers_dec=int((de.bal_primary > 0).sum()),
                   bal_party_dec=de.bal_party.sum() / 1e13, bal_primary_dec=de.bal_primary.sum() / 1e13, bal_nocontract_dec=de.bal_nocontract.sum() / 1e13,
                   share_primary_bal=de.bal_primary.sum() / de.bal_party.sum()))
yr = pd.DataFrame(yr); yr.to_csv(D / "loan_population_by_year.csv", index=False); p(yr.round(3).to_string())
d12 = lm[lm.ym == 140412]
tot_bal_contract = d12.bal_party.sum()
p("12/1404: customers with party balance", len(d12), " with primary balance", int((d12.bal_primary > 0).sum()),
  " party-only (no primary contract, with contract record)", int(((d12.bal_primary == 0) & (d12.bal_nocontract < d12.bal_party)).sum()),
  " only no-contract-record contracts", int((d12.bal_nocontract >= d12.bal_party).sum()))
p("share of primary-basis customers' contracts lacking contract record: customers having any nocontract contract:", int((d12.n_nocontract > 0).sum()))
# گیرنده‌ی اصلی بر پایه‌ی LGC
LGC = set(pd.read_csv(D / "analytic_population_ids.csv").customer_id) if False else None
# ویژگی‌ها
for c in ["bal_party", "bal_primary", "npl_party", "n_party", "n_primary"]:
    x = d12[c]; xl = np.log1p(x.clip(lower=0))
    p(f"  {c:12s} zero-share {(x==0).mean():.3f} skew raw {skew(x):7.1f} skew log {skew(xl):6.2f} p50 {x.median():.3g} p95 {x.quantile(.95):.3g} p99 {x.quantile(.99):.3g}")
pr = d12[d12.bal_primary > 0]
p("primary borrowers 12/1404 npl>0 share: %.4f ; npl-balance share of primary balance %.4f" % ((pr.npl_primary > 0).mean(), pr.npl_primary.sum() / pr.bal_primary.sum()))
p("contracts per primary borrower:", pr.n_primary.describe(percentiles=[.5, .9, .99]).round(2).to_dict())
# سناریوی ماندگاری وام
w = lm[(lm.bal_primary > 0)]
n_by = w.groupby("customer_id").ym.nunique()
p("primary borrowers ever in 60m", len(n_by), " in all 60 months:", int((n_by == 60).sum()), " >=24 months:", int((n_by >= 24).sum()), " >=12:", int((n_by >= 12).sum()))
fr = w.groupby("customer_id").ym.agg(["min", "max"]); p("primary borrowers: first month >140001:", int((fr["min"] > 140001).sum()), "last month <140412 (repaid/exited):", int((fr["max"] < 140412).sum()))
# هم‌پوشانی با سپرده ۱۴۰۴/۱۲
dep12 = set(dm[dm.ym == 140412].customer_id); dep_any = set(dm.customer_id)
prim12 = set(pr.customer_id); party12 = set(d12.customer_id)
p("12/1404 depositors", len(dep12), "primary borrowers in depositors:", len(prim12 & dep12), "of", len(prim12), "; party in depositors:", len(party12 & dep12), "of", len(party12))
p("borrowers (primary) not depositors at 12/1404 but ever depositors:", len((prim12 - dep12) & dep_any), " never:", len(prim12 - dep_any))
# ترکیب رابطه ۱۴۰۴/۱۲: سپرده فقط / سپرده+گیرنده اصلی / سپرده+فقط طرف / وام بدون سپرده
only_dep = dep12 - party12; dep_prim = dep12 & prim12; dep_party_only = (dep12 & party12) - prim12; loan_only = party12 - dep12
p("relationship at 12/1404: deposit only", len(only_dep), "| deposit+primary borrower", len(dep_prim), "| deposit+party only (guarantor/partner)", len(dep_party_only), "| loan party without deposit row", len(loan_only))
# پایداری مرحله: چقدر مشتریان بین سال‌ها از «فقط سپرده» به «گیرنده» می‌روند
def st(ym):
    dd = set(dm[dm.ym == ym].customer_id); l = lm[lm.ym == ym]; pp = set(l[l.bal_primary > 0].customer_id); par = set(l.customer_id) - pp
    return dd, pp, par
pr_y = {}
for y in (1400, 1404):
    dd, pp, par = st(y * 100 + 12); pr_y[y] = (dd, pp, par); p(y, "dep", len(dd), "primary", len(pp), "party-only", len(par))
dd0, pp0, _ = pr_y[1400]; dd4, pp4, _ = pr_y[1404]
p("deposit-only in 1400/12 that became primary borrower by 1404/12:", len((dd0 - pp0) & pp4), "of", len(dd0 - pp0))
p("primary in 1400/12 still primary 1404/12:", len(pp0 & pp4), "of", len(pp0), "; no longer deposit-active:", len(pp0 - dd4))
(D / "loan_feature_profile.txt").write_text("\n".join(log), encoding="utf-8")
