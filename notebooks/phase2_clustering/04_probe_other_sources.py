"""فاز ۲ - الف-۴: کارمزد، سود پرداختی، نوع حساب، شعبه‌ی خانه، پروفایل، طرف‌های وام (فقط خواندن؛ یک Engine)."""
from pathlib import Path
import numpy as np, pandas as pd
from tt_bank.db.connection import get_engine
D = Path(__file__).resolve().parents[2] / "data" / "processed" / "phase2_clustering"
e = get_engine(); q = lambda s: pd.read_sql(s, e)
log = []
def p(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); log.append(s)
def save():
    (D / "probe_other_sources.txt").write_text("\n".join(log), encoding="utf-8")

# ---------- مجموعه‌ی جمعیت‌ها
dep_acc = q("SELECT DISTINCT CAST(LTRIM(RTRIM(MAIN_CUSTOMER_ID)) AS bigint) c FROM dbo.Deposit_Accoutnt_Info WHERE ISNUMERIC(LTRIM(RTRIM(MAIN_CUSTOMER_ID)))=1")
DEP = set(dep_acc.c)
dep_flag = set(q("SELECT DISTINCT CAST(CUSTOMER_ID AS bigint) c FROM dbo.Deposit_Customer").c)
LGC = set(q("SELECT DISTINCT CAST(ID AS bigint) c FROM dbo.Loan_Grant_Customer").c)
LRC = set(q("SELECT DISTINCT CAST(ID AS bigint) c FROM dbo.Loan_Remain_Customer").c)
lci = q("SELECT DISTINCT CAST(MAIN_CUSTOMER_ID AS bigint) c FROM dbo.Loan_Contract_Info")
LCI = set(lci.c)
parties = set(q("SELECT DISTINCT CAST(customer_id AS bigint) c FROM dbo.Loan_Remain").c)
p("depositors (Account_Info)", len(DEP), " Deposit_Customer flag", len(dep_flag), " LGC", len(LGC), " LRC", len(LRC), " LCI main", len(LCI), " Loan_Remain parties (all dates)", len(parties))
p("LGC in DEP", len(LGC & DEP), " LCI main in DEP", len(LCI & DEP), " LCI main in LGC", len(LCI & LGC), " LCI main not in LGC", len(LCI - LGC), " LGC not in LCI", len(LGC - LCI))
p("parties not primary (LCI main or LGC):", len(parties - LCI - LGC), " parties in DEP", len(parties & DEP))
union = DEP | LGC | LCI | parties
p("union of all customer ids:", len(union))
pd.Series(sorted(union), name="customer_id").to_csv(D / "analytic_population_ids.csv", index=False)

# ---------- حساب‌ها
acc = q("""SELECT a.main_customer_id mc, a.deposit_type t, a.open_date od, a.close_date cd FROM dbo.vw_Deposit_Account_Dedup a""")
p("accounts (dedup)", len(acc), " customers", acc.mc.nunique())
tv = acc.t.fillna("(NULL)").str.strip().replace("", "(EMPTY)").value_counts(); p("account type counts:\n" + tv.to_string()); tv.to_csv(D / "account_type_counts.csv")
p("close_date non-empty share", round(acc.cd.fillna("").str.strip().ne("").mean(), 4))
st = q("SELECT LTRIM(RTRIM(STATUS_NAME)) s, COUNT(*) n FROM dbo.Deposit_Accoutnt_Info GROUP BY LTRIM(RTRIM(STATUS_NAME)) ORDER BY 2 DESC"); p("STATUS_NAME:\n" + st.to_string()); st.to_csv(D / "account_status_counts.csv", index=False)
pc = acc.groupby("mc").size().describe(percentiles=[.5, .9, .99]); p("accounts per customer", pc.round(2).to_dict())
tc = acc.assign(t=acc.t.fillna("(NULL)").str.strip()).groupby("mc").t.nunique().value_counts().sort_index().head(8); p("distinct types per customer:", tc.to_dict())
oy = acc.od.fillna("").str[:4]; p("open year range", oy[oy.str.match(r"^\d{4}$")].astype(int).describe().round(0).to_dict())
save()

# ---------- Customer_Monthly_Activity
cma = q("""SELECT main_customer_id c, COUNT(DISTINCT year_mount) n_months, MIN(year_mount) mn, MAX(year_mount) mx FROM dbo.Customer_Monthly_Activity GROUP BY main_customer_id""")
cma["c"] = cma.c.astype("int64"); CMA = set(cma.c)
p("CMA customers", len(CMA), " in DEP", len(CMA & DEP), " share of DEP", round(len(CMA & DEP) / len(DEP), 4), " not in DEP", len(CMA - DEP))
p("CMA months per customer", cma.n_months.describe(percentiles=[.25, .5, .75, .95]).round(1).to_dict())
fc = q("""SELECT code, MAX(title) title, COUNT(DISTINCT main_customer_id) customers, COUNT(*) n_rows, SUM(amount_eq) total, MIN(amount_eq) mn, MAX(amount_eq) mx
          FROM (SELECT DISTINCT main_customer_id, year_mount, code, title, amount_eq FROM dbo.Customer_Monthly_Activity) x GROUP BY code ORDER BY 3 DESC""")
fc.to_csv(D / "fee_codes_summary.csv", index=False, encoding="utf-8-sig"); p("fee codes:", len(fc)); p(fc.head(15).to_string())
neg = q("SELECT COUNT(*) n FROM (SELECT DISTINCT main_customer_id, year_mount, code, amount_eq FROM dbo.Customer_Monthly_Activity WHERE amount_eq<0) x"); p("fee rows negative amount (distinct)", int(neg.n[0]))
save()

# ---------- سود پرداختی سپرده (حساب → مشتری)
ic = q("""SELECT CAST(a.main_customer_id AS bigint) c, i.ym, SUM(i.amt) amt FROM
   (SELECT DISTINCT CAST(Depositid AS numeric(38,0)) did, REPLACE(REPLACE(Year_Mounth,CHAR(13),''),CHAR(10),'') ym, Amount amt FROM dbo.DepositIDInterest) i
   JOIN dbo.vw_Deposit_Account_Dedup a ON a.deposit_id = i.did GROUP BY CAST(a.main_customer_id AS bigint), i.ym""")
ic.to_pickle(D / "interest_customer_month.pkl")
p("interest: customer-month rows", len(ic), " customers", ic.c.nunique(), " share of DEP", round(ic.c.nunique() / len(DEP), 4))
p("interest customers per ym (sample)", ic.groupby("ym").c.nunique().describe().round(0).to_dict())
save()

# ---------- شعبه‌ی خانه
hb = q("SELECT CAST(customer_id AS bigint) c, branch_code, source FROM dbo.Dim_Customer_Home_Branch")
HB = set(hb.c); p("home-branch customers", len(HB), " in DEP", len(HB & DEP), " share of DEP", round(len(HB & DEP) / len(DEP), 4), " in LGC", len(HB & LGC), "of", len(LGC))
p("source counts", hb.source.value_counts().to_dict())
# ---------- پروفایل
cp = q("SELECT COUNT(DISTINCT Customer_id) n FROM dbo.Customer_Profile"); p("Customer_Profile distinct ids", int(cp.n[0]))
cpid = set(q("SELECT DISTINCT CAST(Customer_id AS bigint) c FROM dbo.Customer_Profile").c)
p("Customer_Profile ids matching union population:", len(cpid & union), " matching DEP:", len(cpid & DEP), " matching LGC:", len(cpid & LGC))
rl = q("SELECT LTRIM(RTRIM(REPLACE(real_or_legal,CHAR(34),''))) k, COUNT(*) n FROM (SELECT DISTINCT * FROM dbo.Customer_Profile) x GROUP BY LTRIM(RTRIM(REPLACE(real_or_legal,CHAR(34),'')))"); p("profile real/legal:", rl.to_dict("records"))
save()
