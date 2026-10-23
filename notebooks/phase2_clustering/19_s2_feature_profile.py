"""فاز ۲ - S2: اعتبارسنجی و پروفایل ذخیره‌ی ویژگی (بدون DB)."""
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import skew
D = Path(__file__).resolve().parents[2] / "data" / "processed" / "phase2_clustering"
F = pd.read_pickle(D / "features_customer_year.pkl")
log = []
def p(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); log.append(s)
p("rows", len(F), "unique key", len(F.drop_duplicates(["customer_id", "y"])))
a = F[F.y == 1404]
p("1404 control: sum loan_dec_r (hemat, = record+inferred) %.2f ; sum guar_dec_r %.2f" % (a.loan_dec_r.sum() / 1e13, a.guar_dec_r.sum() / 1e13))
# دامنه‌ها
for c, lo, hi in [("flow_ratio", 0, 1), ("turn_share", 0, 1), ("drawdown", 0, 1), ("npl_share", 0, 1), ("bal_pct", 0, 1)]:
    v = F[c]; p(f"range {c}: min {v.min():.3f} max {v.max():.3f} outside [{lo},{hi}]: {int(((v < lo - 1e-9) | (v > hi + 1e-9)).sum())}")
sh = ["share_long", "share_short", "share_qard", "share_current", "share_special", "share_unknown"]
b = F[F.bal_end_r > 0]
p("type shares sum (bal_end_r>0 & any type bal): mean %.4f ; share of rows with sum in [0.999,1.001]: %.4f" % (b[sh].sum(axis=1).mean(), ((b[sh].sum(axis=1) > .999) & (b[sh].sum(axis=1) < 1.001)).mean()))
p("share_unknown (balance-weighted by bal_end_r) by year:", {int(y): round(float((g.share_unknown * g.bal_end_r).sum() / g.bal_end_r.sum()), 4) for y, g in F.groupby("y")})
# پوشش بلوک‌ها در گروه مدل
M = F[F.category == "model"]
cov = pd.DataFrame({
    "rows_model": len(M),
    "has_loan_dec": M.has_loan_dec.mean(), "has_ledger": M.has_ledger.mean(), "has_interest": M.has_interest.mean(),
    "has_fee_record": M.has_fee_record.mean(), "has_contract_attr": M.has_contract_attr.mean(),
    "province_mapped": M.province.notna().mean(), "type_known(any share>0)": (M[[c for c in sh if c != "share_unknown"]].sum(axis=1) > 0).mean()}, index=["all_years"]).T
p("coverage (category=model, all years):\n" + cov.round(4).to_string())
cy = M.groupby("y").agg(has_loan=("has_loan_dec", "mean"), ledger=("has_ledger", "mean"), interest=("has_interest", "mean"), contract=("has_contract_attr", "mean"),
                        province=("province", lambda s: s.notna().mean()))
p("coverage by year (model):\n" + cy.round(3).to_string()); cy.to_csv(D / "s2_coverage_by_year.csv")
# در میان وام‌داران: پوشش دفتر و صفات قرارداد
L = M[M.has_loan_dec == 1]
p("among borrowers (model, Dec): ledger %.3f  contract attrs %.3f  by year ledger:" % (L.has_ledger.mean(), L.has_contract_attr.mean()), L.groupby("y").has_ledger.mean().round(3).to_dict())
# گمشدگی هر ویژگی عددی در گروه مدل 1404
num = M[M.y == 1404].select_dtypes("number").drop(columns=["customer_id", "y"], errors="ignore")
miss = num.isna().mean().sort_values(ascending=False); p("1404 model: features with NaN share >0:\n" + miss[miss > 0].round(3).to_string())
# توزیع (1404، مدل): چولگی و صفر
core = [c for c in ["bal_mean_r", "bal_end_r", "cr_sum_r", "db_sum_r", "crn_sum", "dbn_sum", "turnover_speed", "ticket_cr_r", "acc_mean", "bal_cv", "bal_trend", "loan_dec_r", "loan_to_dep",
                    "tenure_months", "interest_rate_r", "max_gap", "recency", "turn_share"]]
rows = []
for c in core:
    x = M[M.y == 1404][c].fillna(0); xl = np.sign(x) * np.log1p(np.abs(x))
    rows.append(dict(feature=c, zero_share=(x == 0).mean(), skew_raw=skew(x), skew_log=skew(xl), p50=x.median(), p99=x.quantile(.99)))
pr = pd.DataFrame(rows); pr.to_csv(D / "s2_distribution_1404_model.csv", index=False); p(pr.round(3).to_string())
# همبستگی بالا (اسپیرمن روی نمونه‌ی 100هزار)
S = M[M.y == 1404].sample(100000, random_state=0)
cols = [c for c in S.select_dtypes("number").columns if c not in ("customer_id", "y", "months", "turn_months", "nacc_max", "bal_dec")
        and S[c].nunique() > 5]
cm = S[cols].fillna(0).corr(method="spearman")
hi = [(a_, b_, round(cm.loc[a_, b_], 3)) for i, a_ in enumerate(cols) for b_ in cols[i + 1:] if abs(cm.loc[a_, b_]) >= 0.9]
pd.DataFrame(hi, columns=["f1", "f2", "rho"]).sort_values("rho", key=abs, ascending=False).to_csv(D / "s2_high_corr_pairs.csv", index=False)
p("pairs with |spearman|>=0.9:", len(hi)); [p("  ", h) for h in sorted(hi, key=lambda t: -abs(t[2]))[:25]]
(D / "s2_feature_profile.txt").write_text("\n".join(log), encoding="utf-8")
