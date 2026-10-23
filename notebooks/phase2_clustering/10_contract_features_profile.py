"""فاز ۲ - الف-۳: پوشش و کیفیت صفات قرارداد برای گیرنده‌ی اصلی (بدون DB؛ از pickle خروجی ۰۸)."""
from pathlib import Path
import numpy as np, pandas as pd
D = Path(__file__).resolve().parents[2] / "data" / "processed" / "phase2_clustering"
log = []
def p(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); log.append(s)
c = pd.read_pickle(D / "loan_contract_attrs.pkl"); lgc = set(pd.read_pickle(D / "loan_grant_customer.pkl").c)
for ym in (140412, 140312, 140012):
    r = pd.read_pickle(D / f"loan_remain_{ym}.pkl")
    r["loanfile_id"] = r.loanfile_id.astype("float64").astype("int64"); r["customer_id"] = r.customer_id.astype("float64").astype("int64")
    k = r.groupby("loanfile_id").agg(tot=("tot", "max"), jari=("jari", "max"), eco=("eco", "first"), n_parties=("customer_id", "nunique")).reset_index()
    k = k[k.tot > 0]
    m = k.merge(c, on="loanfile_id", how="left", indicator=True)
    cov = m[m._merge == "both"]
    p(f"=== {ym}: contracts with balance {len(k)} balance(1e13 rial) {k.tot.sum()/1e13:.2f}; with contract record {len(cov)} ({cov.tot.sum()/k.tot.sum():.3f} of balance)")
    prim = cov.groupby("main_customer_id").agg(bal=("tot", "sum"), n=("loanfile_id", "count"), npl=("tot", "sum"))
    npl = (cov.tot - cov.jari).groupby(cov.main_customer_id).sum(); prim["npl"] = npl
    p(f"   primary borrowers (contract-record basis) with balance: {len(prim)}; in Loan_Grant_Customer: {int(prim.index.isin(lgc).sum())}; not in LGC: {int((~prim.index.isin(lgc)).sum())} holding {prim[~prim.index.isin(lgc)].bal.sum()/prim.bal.sum():.3f} of primary balance")
    p("   contracts without record:", int((m._merge == 'left_only').sum()), " their parties distinct:", r[r.loanfile_id.isin(m[m._merge == 'left_only'].loanfile_id)].customer_id.nunique())
    if ym == 140412:
        # صفات
        t = cov.groupby("loan_type_description").agg(n=("loanfile_id", "count"), bal=("tot", "sum")).sort_values("bal", ascending=False)
        p("   distinct loan types:", len(t)); p("   top10 by balance share:", (t.bal / t.bal.sum()).head(10).round(3).to_dict())
        rt = pd.to_numeric(cov.loan_interest_rate.astype(str).str.replace("%", "").str.strip(), errors="coerce")
        p("   interest rate numeric share:", round(rt.notna().mean(), 4), " describe:", rt.describe(percentiles=[.05, .5, .95]).round(2).to_dict())
        p("   rate==0 share:", round((rt == 0).mean(), 4), " rate raw sample values:", cov.loan_interest_rate.astype(str).str.strip().value_counts().head(6).to_dict())
        p("   used_cost>0 share:", round((cov.used_cost > 0).mean(), 4), " grant_amount>0:", round((cov.grant_amount > 0).mean(), 4), " duration_days<=0:", int((cov.duration_days <= 0).sum()), " duration null:", int(cov.duration_days.isna().sum()))
        gy = cov.grant_date.astype(str).str.strip().str[:4]; p("   grant year dist:", gy.value_counts().sort_index().tail(10).to_dict())
        p("   branch code coverage among covered:", round(cov.branch_code.notna().mean(), 4))
        p("   ECO_SEC share of balance (all contracts):", (k.groupby("eco").tot.sum() / k.tot.sum()).round(3).to_dict())
        p("   distinct loan types per primary borrower:", cov.groupby("main_customer_id").loan_type_description.nunique().value_counts().sort_index().head(6).to_dict())
        p("   contracts with >1 party:", round((k.n_parties > 1).mean(), 3), " parties dist:", k.n_parties.describe(percentiles=[.5, .9, .99]).round(1).to_dict())
(D / "contract_features_profile.txt").write_text("\n".join(log), encoding="utf-8")
