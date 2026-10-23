"""فاز ۲ - S2: ذخیره‌ی ویژگی مشتری-سال (1400 تا 1404) از جدول‌های ماهانه‌ی ذخیره‌شده. بدون DB.
قیمت‌ها با نمایه‌ی CPI ماهانه به ریال ثابت 12/1404 تعدیل می‌شوند (ستون‌های *_r). خروجی: features_customer_year.pkl"""
from pathlib import Path
import re
import numpy as np, pandas as pd
import openpyxl

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data" / "processed" / "phase2_clustering"
YEARS = [1400, 1401, 1402, 1403, 1404]
log = []
def p(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); log.append(s)

# ---------------- CPI ماهانه (139901..140408) و برون‌یابی تا 140412
wb = openpyxl.load_workbook(r"D:\OneDrive\My Projects\Bank_Customer_Segmentation\5_New Documents\New_RFM .xlsx", read_only=True, data_only=True)
rows = [(r[1], r[0]) for r in wb["کل سپرده"].iter_rows(min_row=2, values_only=True) if isinstance(r[1], (int, float)) and r[0] is not None]
cpi = pd.Series({int(a): float(b) for a, b in rows}).sort_index()
g = (cpi.loc[140408] / cpi.loc[140308]) ** (1 / 12)       # رشد ماهانه‌ی 12 ماه اخیر برای برون‌یابی
for ym in (140409, 140410, 140411, 140412):
    cpi.loc[ym] = cpi.loc[ym - 1] * g
cpi = cpi.sort_index()
p("CPI months", len(cpi), "first", cpi.index[0], "last", cpi.index[-1], "extrapolated monthly growth %.4f" % (g - 1))
cpi.rename("cpi").to_csv(D / "cpi_monthly_used.csv")
REF = cpi.loc[140412]
def months_all():
    return [y * 100 + m for y in range(1399, 1405) for m in range(1, 13)]
MONTHS = months_all(); MIDX = {ym: i for i, ym in enumerate(MONTHS)}
DEFL = np.array([REF / cpi.loc[ym] for ym in MONTHS])   # ضریب تعدیل هر ماه

# ---------------- پانل
pan = pd.read_pickle(D / "panel_customer_year.pkl")
ids = np.sort(pan.customer_id.unique()); CID = {c: i for i, c in enumerate(ids)}; n = len(ids)
p("customers", n)

# ---------------- ماتریس‌های سپرده
cm = pd.read_pickle(D / "customer_month_deposit.pkl")
ri = cm.customer_id.map(CID); ok = ri.notna().to_numpy()
cm = cm[ok]; ri = ri[ok].to_numpy().astype(np.int64); ci = cm.ym.map(MIDX).to_numpy().astype(np.int64)
shape = (n, len(MONTHS))
def mat(col, dtype=np.float64):
    M = np.zeros(shape, dtype=dtype); M[ri, ci] = cm[col].to_numpy().astype(dtype); return M
BAL, CR, DB = mat("bal"), mat("cr"), mat("db")
CRN, DBN, NACC = mat("crn", np.float32), mat("dbn", np.float32), mat("n_accounts", np.float32)
PRES = np.zeros(shape, dtype=bool); PRES[ri, ci] = True
del cm, ri, ci
BALr, CRr, DBr = BAL * DEFL, CR * DEFL, DB * DEFL
TURN = ((CRN + DBN) > 0) & PRES
first_col = np.where(PRES.any(1), PRES.argmax(1), 10**6)

def pct_rank(x):
    return pd.Series(x).rank(pct=True).to_numpy()

feat = []
for y in YEARS:
    s = (y - 1399) * 12; sl = slice(s, s + 12)
    pres, turn = PRES[:, sl], TURN[:, sl]
    b, cr, db = BALr[:, sl], CRr[:, sl], DBr[:, sl]
    obs_start = np.maximum(first_col, s) - s
    obs = (np.arange(12)[None, :] >= obs_start[:, None])          # ماه‌های درون پنجره‌ی مشاهده
    nobs = obs.sum(1)
    d = pd.DataFrame({"customer_id": ids, "y": y})
    d["obs_months"] = nobs
    d["turn_share"] = np.where(nobs > 0, turn.sum(1) / np.maximum(nobs, 1), 0)
    bm = np.where(nobs > 0, (b * obs).sum(1) / np.maximum(nobs, 1), 0)
    d["bal_mean_r"] = bm
    last_idx = np.where(pres.any(1), 11 - np.argmax(pres[:, ::-1], axis=1), -1)
    d["bal_end_r"] = np.where(last_idx >= 0, b[np.arange(n), np.maximum(last_idx, 0)], 0)
    d["bal_max_r"] = (b * obs).max(1)
    d["bal_min_r"] = np.where(obs, b, np.inf).min(1); d.loc[nobs == 0, "bal_min_r"] = 0
    d["cr_sum_r"], d["db_sum_r"] = (cr * obs).sum(1), (db * obs).sum(1)
    d["crn_sum"], d["dbn_sum"] = CRN[:, sl].sum(1), DBN[:, sl].sum(1)
    tot = d.cr_sum_r + d.db_sum_r
    d["flow_ratio"] = np.where(tot > 0, d.cr_sum_r / np.where(tot > 0, tot, 1), 0.5)
    d["turnover_speed"] = np.where(bm > 0, np.minimum(tot / np.maximum(bm * np.maximum(nobs, 1), 1), 50), 0)
    d["net_flow_ratio"] = np.where(bm > 0, np.clip((d.cr_sum_r - d.db_sum_r) / np.maximum(bm * np.maximum(nobs, 1), 1), -5, 5), 0)
    d["ticket_cr_r"] = np.where(d.crn_sum > 0, d.cr_sum_r / np.maximum(d.crn_sum, 1), 0)
    d["ticket_db_r"] = np.where(d.dbn_sum > 0, d.db_sum_r / np.maximum(d.dbn_sum, 1), 0)
    # وقفه و بازیابی
    run = np.zeros(n); mx = np.zeros(n); lastturn = np.full(n, -1)
    for j in range(12):
        inobs = obs[:, j]; t = turn[:, j]
        run = np.where(inobs & ~t, run + 1, 0); mx = np.maximum(mx, run)
        lastturn = np.where(t, j, lastturn)
    d["max_gap"] = mx
    d["recency"] = np.where(lastturn >= 0, 11 - lastturn, 12)
    # ثبات و روند
    mu = np.where(nobs > 0, (b * obs).sum(1) / np.maximum(nobs, 1), 0)
    sd = np.sqrt(np.where(nobs > 0, (((b - mu[:, None]) ** 2) * obs).sum(1) / np.maximum(nobs, 1), 0))
    d["bal_cv"] = np.where(mu > 0, np.minimum(sd / np.where(mu > 0, mu, 1), 5), 0)
    t_ = np.arange(12)[None, :].astype(float)
    tm = (t_ * obs).sum(1) / np.maximum(nobs, 1)
    cov = (((t_ - tm[:, None]) * (b - mu[:, None])) * obs).sum(1)
    var = (((t_ - tm[:, None]) ** 2) * obs).sum(1)
    slope = np.where(var > 0, cov / np.where(var > 0, var, 1), 0)
    d["bal_trend"] = np.where(mu > 0, np.clip(slope * 12 / np.where(mu > 0, mu, 1), -3, 3), 0)
    d["drawdown"] = np.where(d.bal_max_r > 0, 1 - d.bal_end_r / np.where(d.bal_max_r > 0, d.bal_max_r, 1), 0).clip(0, 1)
    na = NACC[:, sl]
    d["acc_mean"] = np.where(nobs > 0, (na * obs).sum(1) / np.maximum(nobs, 1), 0)
    d["acc_max"] = na.max(1)
    d["acc_change"] = np.where(last_idx >= 0, na[np.arange(n), np.maximum(last_idx, 0)], 0) - np.where(obs.any(1), na[np.arange(n), np.minimum(obs_start, 11)], 0)
    feat.append(d)
F = pd.concat(feat, ignore_index=True)
del BAL, CR, DB, BALr, CRr, DBr, CRN, DBN, NACC, PRES, TURN
p("deposit block rows", len(F))

# ---------------- پرچم و گروه از پانل
keep = ["customer_id", "y", "category", "relationship", "months", "turn_months", "nacc_max", "bal_dec", "in_grant_list", "has_primary_loan"]
F = F.merge(pan[keep], on=["customer_id", "y"], how="inner")
F["bal_pct"] = F.groupby("y").bal_mean_r.rank(pct=True)
p("rows after merge with panel", len(F))

# ---------------- وام (ماهانه‌ی v2؛ قراردادی + استنتاجی)
lm = pd.read_pickle(D / "customer_month_loan_v2.pkl")
lm["y"] = (lm.ym // 100).astype(np.int16)
lm["f"] = lm.ym.map(lambda v: REF / cpi.loc[v])
for c in ["bal_primary", "bal_inferred", "npl_primary", "npl_inferred", "bal_party"]:
    lm[c + "_r"] = lm[c] * lm.f
lm["loan_r"] = lm.bal_primary_r + lm.bal_inferred_r
lm["npl_r"] = lm.npl_primary_r + lm.npl_inferred_r
lm["n_loan"] = lm.n_primary + lm.n_inferred
lm["guar_r"] = (lm.bal_party_r - lm.loan_r).clip(lower=0)
lm["has"] = (lm.loan_r > 0).astype(np.int8)
agg = lm.groupby(["customer_id", "y"]).agg(loan_mean_r=("loan_r", "mean"), loan_months=("has", "sum"),
                                           npl_max_r=("npl_r", "max"), npl_mean_r=("npl_r", "mean"), guar_mean_r=("guar_r", "mean")).reset_index()
d12 = lm[lm.ym % 100 == 12][["customer_id", "y", "loan_r", "npl_r", "n_loan", "guar_r"]].rename(
    columns={"loan_r": "loan_dec_r", "npl_r": "npl_dec_r", "n_loan": "n_loan_dec", "guar_r": "guar_dec_r"})
# ماه نخست وام در سال (وام جدید)
fm = lm[lm.loan_r > 0].groupby("customer_id").ym.min().rename("loan_first_ym").reset_index()
F = F.merge(agg, on=["customer_id", "y"], how="left").merge(d12, on=["customer_id", "y"], how="left").merge(fm, on="customer_id", how="left")
for c in ["loan_mean_r", "loan_months", "npl_max_r", "npl_mean_r", "guar_mean_r", "loan_dec_r", "npl_dec_r", "n_loan_dec", "guar_dec_r"]:
    F[c] = F[c].fillna(0)
F["has_loan_dec"] = (F.loan_dec_r > 0).astype(np.int8)
F["loan_new_in_year"] = ((F.loan_first_ym // 100) == F.y).astype(np.int8)
F["loan_to_dep"] = np.where(F.loan_dec_r > 0, F.loan_dec_r / (F.bal_end_r + 1e5), 0).clip(0, 500)
F["npl_share"] = np.where(F.loan_dec_r > 0, F.npl_dec_r / np.where(F.loan_dec_r > 0, F.loan_dec_r, 1), 0).clip(0, 1)
F["has_npl"] = (F.npl_dec_r > 0).astype(np.int8)
del lm

# ---------------- دفتر اقساط (گیرنده‌ی قراردادی)
lg = pd.read_pickle(D / "customer_month_ledger.pkl")
lg["cid"] = lg.cid.astype("float64").astype("int64"); lg["y"] = (lg.due_ym // 100).astype(np.int16)
lg = lg[(lg.due_ym >= 140001) & (lg.due_ym <= 140412)]
la = lg.groupby(["cid", "y"]).agg(n_inst=("n_inst", "sum"), n_late=("n_late", "sum"), n_late30=("n_late30", "sum"), n_late90=("n_late90", "sum"),
                                 max_dpd=("max_dpd", "max"), sum_dpd=("sum_dpd", "sum"), s_main=("s_main", "sum"), s_pen=("s_pen", "sum"),
                                 n_moaavagh=("n_moaavagh", "sum"), n_mashkoo=("n_mashkoo", "sum")).reset_index().rename(columns={"cid": "customer_id"})
la["late30_share"] = la.n_late30 / la.n_inst
la["late90_share"] = la.n_late90 / la.n_inst
la["late_share"] = la.n_late / la.n_inst
la["mean_dpd"] = (la.sum_dpd / la.n_inst).clip(-30, 365)
la["max_dpd_c"] = la.max_dpd.clip(-30, 365)
la["penalty_ratio"] = (la.s_pen / np.maximum(la.s_main, 1)).clip(0, 1)
la["bad_status_share"] = (la.n_moaavagh + la.n_mashkoo) / la.n_inst
F = F.merge(la[["customer_id", "y", "n_inst", "late_share", "late30_share", "late90_share", "mean_dpd", "max_dpd_c", "penalty_ratio", "bad_status_share"]],
            on=["customer_id", "y"], how="left")
F["has_ledger"] = F.n_inst.notna().astype(np.int8)
del lg, la

# ---------------- سود پرداختی
ic = pd.read_pickle(D / "interest_customer_month.pkl")
ic["ym"] = ic.ym.astype(str).str.strip().astype(int)
ic = ic[(ic.ym >= 140001) & (ic.ym <= 140412)]
ic["amt_r"] = ic.amt * ic.ym.map(lambda v: REF / cpi.loc[v])
ic["y"] = (ic.ym // 100).astype(np.int16)
ia = ic.groupby(["c", "y"]).agg(interest_months=("ym", "nunique"), interest_sum_r=("amt_r", "sum")).reset_index().rename(columns={"c": "customer_id"})
F = F.merge(ia, on=["customer_id", "y"], how="left")
F["interest_months"] = F.interest_months.fillna(0); F["interest_sum_r"] = F.interest_sum_r.fillna(0)
F["has_interest"] = (F.interest_months > 0).astype(np.int8)
F["interest_rate_r"] = np.where((F.interest_sum_r > 0) & (F.bal_mean_r > 0), F.interest_sum_r / np.maximum(F.bal_mean_r, 1e5), 0).clip(0, 3)
del ic, ia

# ---------------- کارمزد
fe = pd.read_pickle(D / "fee_customer_month_code.pkl")
fe["y"] = (fe.ym // 100).astype(np.int16); fe["code"] = fe.code.astype(str).str.strip()
fe = fe[(fe.y >= 1400) & (fe.y <= 1404)]
fp = fe.pivot_table(index=["c", "y"], columns="code", values="n", aggfunc="sum", fill_value=0).reset_index().rename(columns={"c": "customer_id"})
fp.columns = [("fee_" + str(c) if c not in ("customer_id", "y") else c) for c in fp.columns]
F = F.merge(fp, on=["customer_id", "y"], how="left")
for c in [c for c in F.columns if c.startswith("fee_")]:
    F[c] = F[c].fillna(0)
F["has_fee_record"] = (F.filter(like="fee_").sum(axis=1) > 0).astype(np.int8)
del fe, fp

# ---------------- ساختار حساب (پایان هر سال)
def tgroup(t):
    t = str(t)
    if "بلند" in t: return "long"
    if "ویژه" == t.strip() or t.strip() == "ویژه": return "special"
    if "کوتاه" in t: return "short"
    if "قرض" in t: return "qard"
    if "جاری" in t: return "current"
    return "unknown"
tb = []
for ym in (140012, 140112, 140212, 140312, 140412):
    t = pd.read_pickle(D / f"deposit_type_balance_{ym}.pkl")
    t["grp"] = t.typ.map(tgroup); t["y"] = ym // 100
    tb.append(t)
tb = pd.concat(tb, ignore_index=True)
tp = tb.pivot_table(index=["customer_id", "y"], columns="grp", values="bal", aggfunc="sum", fill_value=0)
tot = tp.sum(axis=1).replace(0, np.nan)
tsh = tp.div(tot, axis=0).add_prefix("share_").reset_index()
ntypes = (tb[tb.grp != "unknown"].groupby(["customer_id", "y"]).grp.nunique().rename("n_types").reset_index())
F = F.merge(tsh, on=["customer_id", "y"], how="left").merge(ntypes, on=["customer_id", "y"], how="left")
for c in [c for c in F.columns if c.startswith("share_")]:
    F[c] = F[c].fillna(0)
F["n_types"] = F.n_types.fillna(0)
# سهم‌های نرمال‌شده بر مانده‌ی دارای نوع (برای پایداری زمانی؛ در سال‌های قبل نوع بخشی از مانده ثبت نشده است)
known = (1 - F.share_unknown).replace(0, np.nan)
for g_ in ["long", "short", "qard", "current", "special"]:
    F[f"share_{g_}_k"] = (F[f"share_{g_}"] / known).fillna(0).clip(0, 1)
del tb, tp, tsh

# ---------------- قدمت و وضعیت حساب
ac = pd.read_pickle(D / "account_open_status.pkl")
ac["oy"] = pd.to_numeric(ac.od.str[:4], errors="coerce"); ac["om"] = pd.to_numeric(ac.od.str[5:7], errors="coerce")
ac = ac[(ac.oy >= 1350) & (ac.oy <= 1405) & ac.om.between(1, 12)]
ac["ordm"] = ac.oy * 12 + ac.om
first_open = ac.groupby("c").ordm.min().rename("first_open").reset_index().rename(columns={"c": "customer_id"})
blocked = ac.assign(b=(ac.st != "باز").astype(int)).groupby("c").b.max().rename("has_blocked_account").reset_index().rename(columns={"c": "customer_id"})
F = F.merge(first_open, on="customer_id", how="left").merge(blocked, on="customer_id", how="left")
F["tenure_months"] = (F.y * 12 + 12 - F.first_open).clip(lower=0)
F["tenure_months"] = F.tenure_months.fillna(F.tenure_months.median())
F["has_blocked_account"] = F.has_blocked_account.fillna(0)
F = F.drop(columns="first_open")

# ---------------- قرارداد: صفات مالک (قراردادی یا استنتاجی) در 12 هر سال
attrs = pd.read_pickle(D / "loan_contract_attrs.pkl")
attrs["rate"] = pd.to_numeric(attrs.loan_interest_rate.astype(str).str.replace("%", "").str.strip(), errors="coerce")
attrs["gy"] = pd.to_numeric(attrs.grant_date.astype(str).str.strip().str[:4], errors="coerce")
attrs["gm"] = pd.to_numeric(attrs.grant_date.astype(str).str.strip().str[5:7], errors="coerce")
def tgrp(t):
    t = str(t).replace("ي", "ی").replace("ك", "ک")   # نرمال‌سازی ي و ك عربی (اصلاح 2026-10-22: «فروش اقساطي» و «خريد دين» قبلاً تطبیق نمی‌خورد)
    for k, v in [("قرض الحسنه", "qard"), ("مرابحه", "murabaha"), ("مشارکت", "partnership"), ("فروش اقساطی", "installment"), ("خرید دین", "debt_purchase"),
                 ("جعاله", "jo'ala"), ("مضاربه", "mudaraba")]:
        if k in t: return v
    return "other"
attrs["tgrp"] = attrs.loan_type_description.map(tgrp)
ecomap = {"خدمات": "services", "صنعتی": "industry", "مسکن و ساختمان": "housing", "کشاورزی": "agri", "بازرگانی": "trade"}
contract_feats = []
for ym in (140012, 140112, 140212, 140312, 140412):
    r = pd.read_pickle(D / f"loan_remain_{ym}.pkl")
    for k in ("loanfile_id", "customer_id"):
        r[k] = r[k].astype("float64").astype("int64")
    k = r.groupby("loanfile_id").agg(bal=("tot", "max"), n=("customer_id", "nunique"), first=("customer_id", "min"), eco=("eco", "first")).reset_index()
    k = k[k.bal > 0].merge(attrs, on="loanfile_id", how="left")
    k["owner"] = k.main_customer_id.where(k.main_customer_id.notna(), np.where(k.n == 1, k["first"], np.nan))
    k = k[k.owner.notna()].copy(); k["owner"] = k.owner.astype("int64")
    y = ym // 100
    k["age_m"] = (y * 12 + 12 - (k.gy * 12 + k.gm)).clip(lower=0)
    k["coll"] = np.where(k.grant_amount > 0, (k.used_cost / k.grant_amount).clip(0, 5), np.nan)
    has_rec = k.main_customer_id.notna()
    rec = k[has_rec]
    def wavg(df, col):
        w = df.bal.where(df[col].notna(), 0)
        return (df[col].fillna(0) * w).groupby(df.owner).sum() / w.groupby(df.owner).sum().replace(0, np.nan)
    out = pd.DataFrame({"n_contracts_dec": k.groupby("owner").size(),
                        "rate_w": wavg(rec, "rate"), "age_w": wavg(rec, "age_m"), "coll_w": wavg(rec, "coll"),
                        "duration_w": wavg(rec.assign(dur=rec.duration_days.clip(0, 5000)), "dur"),
                        "norecord_share": (k.bal.where(~has_rec, 0)).groupby(k.owner).sum() / k.groupby("owner").bal.sum()})
    tot = k.groupby("owner").bal.sum()
    for g_ in ["qard", "murabaha", "partnership", "installment", "debt_purchase", "other"]:
        out["ltype_" + g_] = (rec.bal.where(rec.tgrp == g_, 0)).groupby(rec.owner).sum() / rec.groupby("owner").bal.sum().replace(0, np.nan)
    k["ecog"] = k.eco.map(ecomap).fillna("other_sector")
    for g_ in ["services", "industry", "housing", "agri", "trade", "other_sector"]:
        out["sector_" + g_] = (k.bal.where(k.ecog == g_, 0)).groupby(k.owner).sum() / tot
    out = out.reset_index().rename(columns={"owner": "customer_id"}); out["y"] = y
    contract_feats.append(out)
CF = pd.concat(contract_feats, ignore_index=True); CF["y"] = CF.y.astype(F.y.dtype)
F = F.merge(CF, on=["customer_id", "y"], how="left")
F["has_contract_attr"] = F.rate_w.notna().astype(np.int8)

# ---------------- جغرافیا
hb = pd.read_pickle(D / "home_branch.pkl"); hb["branch_code"] = hb.branch_code.astype(str).str.replace("\r", "").str.strip()
pm = pd.read_csv(ROOT / "data" / "processed" / "phase1_market_overview" / "official_branch_province_map.csv", dtype={"branch_code": str})
pm = pm.drop_duplicates("branch_code")
hb = hb.merge(pm[["branch_code", "province"]], on="branch_code", how="left").rename(columns={"c": "customer_id", "branch_code": "home_branch", "source": "home_source"})
F = F.merge(hb[["customer_id", "home_branch", "province", "home_source"]], on="customer_id", how="left")
p("home branch coverage in panel: %.3f ; province mapped: %.3f" % (F.home_branch.notna().mean(), F.province.notna().mean()))

# ---------------- ذخیره
F = F.sort_values(["y", "customer_id"]).reset_index(drop=True)
F.to_pickle(D / "features_customer_year.pkl")
p("features rows", len(F), "columns", F.shape[1])
# کنترل جمع‌ها (اسمی): مانده‌ی 12/هر سال
c = F.groupby("y").agg(customers=("customer_id", "size"), bal_dec_nominal=("bal_dec", "sum"))
c["bal_dec_nominal"] = c.bal_dec_nominal / 1e13
p("control (nominal Dec balance, hemat):", c.round(2).to_dict("index"))
pd.Series(log).to_csv(D / "s2_build_log.txt", index=False, header=False)
