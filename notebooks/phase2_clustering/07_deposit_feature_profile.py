"""فاز ۲ - الف-۲/۵: پروفایل ویژگی‌های سپرده در سطح مشتری-سال، چولگی، همبستگی، پایداری سالانه، پرت‌ها (بدون DB؛ از pickle)."""
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import spearmanr, skew
D = Path(__file__).resolve().parents[2] / "data" / "processed" / "phase2_clustering"
cm = pd.read_pickle(D / "customer_month_deposit.pkl")
log = []
def p(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); log.append(s)
cm["y"] = cm.ym // 100
cm["turn"] = ((cm.crn + cm.dbn) > 0).astype(np.int8)
# --- پرت‌ها: تعداد حساب و مانده در 140412
d = cm[cm.ym == 140412].sort_values("bal", ascending=False)
p("top10 balance share 140412: %.4f ; top100: %.4f ; top1%%: %.4f ; top10%%: %.4f" % (
    d.bal.head(10).sum() / d.bal.sum(), d.bal.head(100).sum() / d.bal.sum(),
    d.bal.head(int(len(d) * .01)).sum() / d.bal.sum(), d.bal.head(int(len(d) * .10)).sum() / d.bal.sum()))
p("top 10 customers 140412 (id, accounts, balance 1e9 rial, credit 1e9):")
for r in d.head(10).itertuples(): p("  ", r.customer_id, int(r.n_accounts), round(r.bal / 1e9, 1), round(r.cr / 1e9, 1))
p("customers with >=50 accounts:", int((d.n_accounts >= 50).sum()), " >=100:", int((d.n_accounts >= 100).sum()), " >=1000:", int((d.n_accounts >= 1000).sum()))
big = d[d.n_accounts >= 100]; p("their balance share: %.4f" % (big.bal.sum() / d.bal.sum()))
# --- ویژگی‌های سالانه
def yearly(g):
    f = pd.DataFrame({
        "months": g.groupby("customer_id").ym.nunique(),
        "turn_months": g.groupby("customer_id").turn.sum(),
        "bal_mean": g.groupby("customer_id").bal.mean(),
        "bal_end": g.sort_values("ym").groupby("customer_id").bal.last(),
        "bal_cv": g.groupby("customer_id").bal.std() / g.groupby("customer_id").bal.mean().replace(0, np.nan),
        "cr_sum": g.groupby("customer_id").cr.sum(), "db_sum": g.groupby("customer_id").db.sum(),
        "crn_sum": g.groupby("customer_id").crn.sum(), "dbn_sum": g.groupby("customer_id").dbn.sum(),
        "acc_mean": g.groupby("customer_id").n_accounts.mean()})
    return f
Y = {y: yearly(cm[cm.y == y]) for y in range(1399, 1405)}
for y in (1400, 1404):
    f = Y[y]; p(f"--- year {y}: customers {len(f)}")
    for c in ["bal_mean", "cr_sum", "db_sum", "crn_sum", "dbn_sum", "acc_mean", "bal_cv"]:
        x = f[c].dropna(); xl = np.log1p(x.clip(lower=0))
        p(f"  {c:9s} zero-share {(x==0).mean():.3f}  skew raw {skew(x):8.1f}  skew log1p {skew(xl):6.2f}  p50 {x.median():.3g} p99 {x.quantile(.99):.3g}")
    p("  months<12 share:", round((f.months < 12).mean(), 3), "   turn_months==0 share:", round((f.turn_months == 0).mean(), 3))
    L = np.log1p(f[["bal_mean", "cr_sum", "db_sum", "crn_sum", "dbn_sum", "acc_mean"]].clip(lower=0))
    p("  spearman matrix (log vars) =\n" + L.corr(method="spearman").round(2).to_string())
# --- پایداری سالانه: ماندن در دهک، همبستگی
p("--- year-to-year stability of mean balance (customers present both years, full 12 months both)")
for a, b in [(1400, 1401), (1401, 1402), (1402, 1403), (1403, 1404), (1400, 1404)]:
    j = Y[a][Y[a].months == 12].join(Y[b][Y[b].months == 12], lsuffix="_a", rsuffix="_b", how="inner")
    rho = spearmanr(j.bal_mean_a, j.bal_mean_b).statistic
    qa = pd.qcut(j.bal_mean_a.rank(method="first"), 5, labels=False); qb = pd.qcut(j.bal_mean_b.rank(method="first"), 5, labels=False)
    p(f"  {a}->{b}: n={len(j)} spearman={rho:.3f} quintile stay={np.mean(qa==qb):.3f} moved>=2 quintiles={np.mean(abs(qa-qb)>=2):.3f}")
# --- فصلی‌بودن
s = cm[(cm.ym >= 140001)].groupby(cm.ym % 100).agg(cr=("cr", "sum"), db=("db", "sum"), turn=("turn", "mean"))
p("seasonality (month-of-year, share of total credit):", (s.cr / s.cr.sum()).round(3).to_dict())
# --- ورود: سال نخستین ردیف و جمعیت
first = cm.groupby("customer_id").ym.min(); fy = (first // 100).value_counts().sort_index(); p("first-row year counts:", fy.to_dict())
last = cm.groupby("customer_id").ym.max(); p("customers with last row < 140412:", int((last < 140412).sum()))
# --- همبستگی ورود با مانده‌ی اولیه
(D / "deposit_feature_profile.txt").write_text("\n".join(log), encoding="utf-8")
