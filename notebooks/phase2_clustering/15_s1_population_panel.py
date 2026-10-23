"""فاز ۲ - S1: تثبیت جمعیت و پانل مشتری-سال (۱۴۰۰ تا ۱۴۰۴). فقط از pickle ها؛ بدون DB.
خروجی‌ها: panel_customer_year.pkl (+ csv.gz)، جدول‌های خلاصه، جدول تطبیق تعریف گیرنده‌ی اصلی، کنترل جمع‌ها."""
from pathlib import Path
import numpy as np, pandas as pd

D = Path(__file__).resolve().parents[2] / "data" / "processed" / "phase2_clustering"
THR_INST, THR_BAL, MIN_MONTHS, MIN_TURN = 100, 5_000_000, 6, 3
log = []
def p(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); log.append(s)

# ---------- سپرده
cm = pd.read_pickle(D / "customer_month_deposit.pkl")
cm["y"] = (cm.ym // 100).astype(np.int16)
cm["turn"] = ((cm.crn + cm.dbn) > 0).astype(np.int8)
first_ym = cm.groupby("customer_id").ym.min().rename("first_ym")
last_ym = cm.groupby("customer_id").ym.max().rename("last_ym")
g = cm.groupby(["customer_id", "y"])
pan = g.agg(months=("ym", "nunique"), turn_months=("turn", "sum"), bal_mean=("bal", "mean"), bal_max=("bal", "max"),
            nacc_mean=("n_accounts", "mean"), cr_sum=("cr", "sum"), db_sum=("db", "sum"), crn_sum=("crn", "sum"), dbn_sum=("dbn", "sum"),
            nacc_max=("n_accounts", "max")).reset_index()
dec = cm[cm.ym % 100 == 12][["customer_id", "y", "bal"]].rename(columns={"bal": "bal_dec"})
pan = pan.merge(dec, on=["customer_id", "y"], how="left").merge(first_ym, on="customer_id").merge(last_ym, on="customer_id")
pan = pan[pan.y >= 1400].copy()
del cm

# ---------- تسهیلات (پایان هر سال؛ نسخه‌ی 2 با گیرنده‌ی استنتاجی در همه‌ی ماه‌ها)
lm = pd.read_pickle(D / "customer_month_loan_v2.pkl")
lm["y"] = (lm.ym // 100).astype(np.int16)
ldec = lm[lm.ym % 100 == 12][["customer_id", "y", "bal_party", "bal_primary", "bal_nocontract", "npl_primary", "bal_inferred", "npl_inferred"]]
lany = lm[(lm.bal_primary > 0) | (lm.bal_inferred > 0)].groupby(["customer_id", "y"]).ym.nunique().rename("loan_months").reset_index()
pan = pan.merge(ldec, on=["customer_id", "y"], how="left").merge(lany, on=["customer_id", "y"], how="left")
for c in ["bal_party", "bal_primary", "bal_nocontract", "npl_primary", "bal_inferred", "npl_inferred", "loan_months"]:
    pan[c] = pan[c].fillna(0)
del lm

# ---------- سطح رابطه در پایان سال
lgc = set(pd.read_pickle(D / "loan_grant_customer.pkl").c)
pan["in_grant_list"] = pan.customer_id.isin(lgc)
rel = np.select([pan.bal_primary > 0, pan.bal_inferred > 0, pan.bal_party > 0],
                ["primary_record", "primary_inferred", "party_only"], default="deposit_only")
pan["relationship"] = rel

# ---------- گروه‌بندی طبق D3
newc = (pan.first_ym // 100 == pan.y) & (pan.months < MIN_MONTHS)
inst = pan.nacc_max >= THR_INST
has_loan = (pan.loan_months > 0) | (pan.bal_primary > 0) | (pan.bal_inferred > 0)
pan["has_primary_loan"] = has_loan
idle = (pan.months >= MIN_MONTHS) & ((pan.turn_months < MIN_TURN) | (pan.bal_max < THR_BAL)) & ~has_loan
mod = (pan.months >= MIN_MONTHS) & ~idle
pan["category"] = np.select([inst, newc, mod, idle], ["institutional_candidate", "newcomer", "model", "idle_token"], default="partial_other")

pan.to_pickle(D / "panel_customer_year.pkl")
pan.to_csv(D / "panel_customer_year.csv.gz", index=False, compression="gzip")
p("panel rows", len(pan), "customers", pan.customer_id.nunique())

# ---------- جدول‌های خلاصه
t = pan.groupby(["y", "category"]).agg(customers=("customer_id", "size"), bal_mean_sum=("bal_mean", "sum")).reset_index()
t["share_customers"] = t.customers / t.groupby("y").customers.transform("sum")
t["share_balance"] = t.bal_mean_sum / t.groupby("y").bal_mean_sum.transform("sum")
t["bal_mean_sum_hemat"] = t.bal_mean_sum / 1e13
t.drop(columns="bal_mean_sum").to_csv(D / "s1_category_by_year.csv", index=False)
p("--- category by year (customers)"); p(t.pivot(index="y", columns="category", values="customers").fillna(0).astype(int).to_string())
p("--- category by year (share of average balance)"); p(t.pivot(index="y", columns="category", values="share_balance").round(3).to_string())
r = pan.groupby(["y", "relationship"]).size().unstack(fill_value=0); r["total"] = r.sum(axis=1)
r.to_csv(D / "s1_relationship_by_year.csv"); p("--- relationship at year end"); p(r.to_string())
rm = pan[pan.category == "model"].groupby(["y", "relationship"]).size().unstack(fill_value=0); rm.to_csv(D / "s1_relationship_model_by_year.csv")
p("--- relationship among model-category"); p(rm.to_string())

# ---------- تطبیق تعریف‌های گیرنده‌ی اصلی در 12/1404
a = pan[pan.y == 1404]
prim_rec = a[a.bal_primary > 0]; prim_inf = a[(a.bal_primary == 0) & (a.bal_inferred > 0)]
tot = len(a)
rows = [("فهرست رسمی Loan_Grant_Customer (کل فهرست)", len(lgc)),
        ("گیرنده‌ی اصلی بر پایه‌ی قرارداد (مانده‌ی مثبت 12/1404)", len(prim_rec)),
        ("  از آن: عضو فهرست رسمی", int(prim_rec.in_grant_list.sum())),
        ("گیرنده‌ی اصلی استنتاجی (طرف یگانه‌ی قرارداد بدون رکورد)", len(prim_inf)),
        ("مجموع گیرنده‌ی اصلی (قراردادی + استنتاجی)", len(prim_rec) + len(prim_inf)),
        ("فقط ضامن/شریک", int((a.relationship == "party_only").sum())),
        ("فقط سپرده", int((a.relationship == "deposit_only").sum()))]
rec = pd.DataFrame(rows, columns=["item", "customers"]); rec["share_of_depositors"] = rec.customers / tot
rec.to_csv(D / "s1_primary_definition_reconciliation.csv", index=False, encoding="utf-8-sig"); p(rec.to_string())
dep_only_share = {"فهرست رسمی": 1 - (tot and (a.in_grant_list.sum() / tot)),
                  "قراردادی": (a.relationship != "primary_record").mean(),
                  "قراردادی+استنتاجی": a.relationship.isin(["deposit_only", "party_only"]).mean()}
p("share without primary loan by definition:", {k: round(float(v), 4) for k, v in dep_only_share.items()})

# ---------- کنترل جمع‌ها (12 هر سال)
c = pan.groupby("y").agg(depositors=("customer_id", "size"), bal_dec=("bal_dec", "sum"), loan_party=("bal_party", "sum"),
                         loan_primary_rec=("bal_primary", "sum"), loan_nocontract=("bal_nocontract", "sum"), loan_inferred=("bal_inferred", "sum"))
for k in ["bal_dec", "loan_party", "loan_primary_rec", "loan_nocontract", "loan_inferred"]:
    c[k] = c[k] / 1e13
c.round(2).to_csv(D / "s1_control_totals.csv"); p("--- control totals (hemat = 1e13 rial)"); p(c.round(2).to_string())

# ---------- تکرارپذیری هسته‌ی پایدار
elig = pan[pan.category == "model"].groupby("customer_id").y.nunique()
p("customers in model category in k of 5 years:", elig.value_counts().sort_index().to_dict())
(D / "s1_summary.txt").write_text("\n".join(log), encoding="utf-8")
