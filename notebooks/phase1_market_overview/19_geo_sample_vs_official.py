"""مقایسه‌ی استانی نمونه با آمار رسمی بانک (۱۲/۱۴۰۴) و پراکندگی جغرافیایی مشتریان نمونه.

خروجی‌ها (data/processed/phase1_market_overview):
- province_sample_vs_official_140412.csv : تسهیلات و سپرده‌ی نمونه (به تفکیک استان) در برابر آمار رسمی
- province_customers_home_branch.csv     : تعداد مشتری و مانده‌ی سپرده‌ی نمونه به تفکیک استان شعبه‌ی اصلی

شعب فقط با کد کار می‌شوند. یک Engine؛ اجرا: python -u مستقیم.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from tt_bank.db.connection import get_engine

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed" / "phase1_market_overview"
NONGEO = ["ستاد", "ستاد-امورمالی", "شعب مستقل"]


def main() -> None:
    engine = get_engine()
    bmap = pd.read_csv(PROC / "official_branch_province_map.csv")
    bmap["branch_code"] = bmap.branch_code.astype(str)
    prov_of = dict(zip(bmap.branch_code, bmap.province))

    off = pd.read_csv(PROC / "bank_official_monthly_by_province.csv")
    off = off[off.year_month == 140412][["province", "rial_resources", "loans"]]

    # تسهیلات نمونه به تفکیک شعبه (بخش دارای نگاشت شعبه)
    loans = pd.read_sql(
        "SELECT branch_code, SUM(total_balance) AS bal FROM dbo.vw_Loan_Remain_By_Branch_Month "
        "WHERE year_month = 140412 AND branch_code IS NOT NULL GROUP BY branch_code", engine)
    loans["province"] = loans.branch_code.astype(str).map(prov_of)
    print("loan branches unmapped:", int(loans.province.isna().sum()), flush=True)
    sample_loans = loans.dropna(subset=["province"]).groupby("province").bal.sum()

    # مشتریان به تفکیک استان شعبه‌ی اصلی + مانده‌ی سپرده‌ی ۱۲/۱۴۰۴
    chb = pd.read_csv(PROC / "customer_home_branch.csv", usecols=["customer_id", "branch_code"])
    chb["province"] = chb.branch_code.astype("Int64").astype(str).map(prov_of)
    bal = pd.read_sql(
        "SELECT customer_id, SUM(avr_total_amount_eq) AS bal FROM dbo.Deposit_Monthly_Activity WHERE year_mount = 140412 GROUP BY customer_id",
        engine)
    bal["customer_id"] = bal.customer_id.astype("int64")
    chb["customer_id"] = chb.customer_id.astype("int64")
    m = chb.merge(bal, on="customer_id", how="left").fillna({"bal": 0.0})
    print("customers", len(chb), "province-mapped", int(m.province.notna().sum()), flush=True)
    cust = m.dropna(subset=["province"]).groupby("province").agg(customers=("customer_id", "count"), deposit=("bal", "sum"))
    cust.reset_index().to_csv(PROC / "province_customers_home_branch.csv", index=False, encoding="utf-8-sig")

    o = off.set_index("province")
    res = pd.DataFrame({"official_loans": o.loans, "official_resources": o.rial_resources})
    res["sample_loans"] = sample_loans
    res["sample_deposit_inferred"] = cust.deposit
    res = res.fillna(0.0)
    res.reset_index().rename(columns={"index": "province"}).to_csv(
        PROC / "province_sample_vs_official_140412.csv", index=False, encoding="utf-8-sig")
    geo = res.drop(index=[p for p in NONGEO if p in res.index])
    print(geo.assign(cov=geo.sample_loans / geo.official_loans).round(3).head(40).to_string())
    for a, b in (("sample_loans", "official_loans"), ("sample_deposit_inferred", "official_resources")):
        r = np.corrcoef(np.log(geo[a].clip(lower=1)), np.log(geo[b]))[0, 1]
        print(a, "vs", b, "log-pearson", round(r, 3), flush=True)


if __name__ == "__main__":
    main()
