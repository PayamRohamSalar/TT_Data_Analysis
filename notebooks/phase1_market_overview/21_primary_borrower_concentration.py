"""تمرکز مانده‌ی تسهیلات بر مبنای گیرنده‌ی اصلی (۱۲/۱۴۰۴) و مقایسه با تمرکز سپرده.

مانده‌ی هر قرارداد به گیرنده‌ی اصلی همان قرارداد نسبت داده می‌شود (همان منطق اسکریپت ۱۷).
سپرده: مانده‌ی ماه ۱۴۰۴/۱۲ هر سپرده‌گذار از خروجی deposit_balance_ladder (فقط برای صدک‌ها از DB).

خروجی: data/processed/phase1_market_overview/concentration_primary_borrower.csv
فقط یک Engine (SQL Server تک‌کاربره)؛ اجرا: python -u مستقیم.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from tt_bank.db.connection import get_engine

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "processed" / "phase1_market_overview"
YM = 140412


def top_shares(bal: pd.Series, pcts=(1, 5, 10, 20)) -> dict:
    s = np.sort(bal[bal > 0].to_numpy())[::-1]
    tot = s.sum()
    return {p: round(100 * s[: max(1, int(np.ceil(len(s) * p / 100)))].sum() / tot, 1) for p in pcts}, len(s), tot


def main() -> None:
    engine = get_engine()
    info = pd.read_sql(
        "SELECT DISTINCT CAST(LOANFILE_ID AS numeric(38,0)) AS loanfile_id, "
        "CAST(LTRIM(RTRIM(MAIN_CUSTOMER_ID)) AS numeric(38,0)) AS main_id "
        "FROM dbo.Loan_Contract_Info WHERE ISNUMERIC(LTRIM(RTRIM(MAIN_CUSTOMER_ID))) = 1", engine).drop_duplicates("loanfile_id")
    df = pd.read_sql(
        f"SELECT customer_id, loanfile_id, MAX(Total_Remain) AS bal FROM dbo.Loan_Remain "
        f"WHERE Transaction_Date BETWEEN {YM * 100 + 1} AND {YM * 100 + 31} GROUP BY customer_id, loanfile_id", engine)
    c = df.groupby("loanfile_id").agg(bal=("bal", "max"), nparties=("customer_id", "nunique"),
                                      first_party=("customer_id", "min")).reset_index().merge(info, on="loanfile_id", how="left")
    c["owner"] = c.main_id
    single = c.owner.isna() & (c.nparties == 1)
    c.loc[single, "owner"] = c.loc[single, "first_party"]
    matched = c.dropna(subset=["owner"])
    print("contracts", len(c), "attributed", len(matched), "bal share attributed",
          round(matched.bal.sum() / c.bal.sum(), 4), flush=True)
    per_main = matched.groupby("owner").bal.sum()
    grant = set(pd.read_sql("SELECT DISTINCT ID AS customer_id FROM dbo.Loan_Grant_Customer", engine)["customer_id"])
    in_grant = per_main.index.isin(grant)
    print("main owners", len(per_main), "in Loan_Grant_Customer", int(in_grant.sum()),
          "balance share in grant list", round(per_main[in_grant].sum() / per_main.sum(), 4), flush=True)
    per_primary = per_main[in_grant]
    all_parties = df.groupby("customer_id").bal.sum()

    rows = []
    for name, ser in (("تسهیلات: گیرنده‌ی اصلی", per_primary), ("تسهیلات: صاحب قرارداد (MAIN_CUSTOMER_ID)", per_main), ("تسهیلات: تمام طرفین", all_parties)):
        sh, n, tot = top_shares(ser)
        print(name, n, tot / 1e13, sh)
        rows += [dict(basis=name, top_pct=p, share_pct=v, customers=n, total_thousand_bn_toman=tot / 1e13) for p, v in sh.items()]

    dep = pd.read_sql(
        f"SELECT customer_id, SUM(avr_total_amount_eq) AS bal FROM dbo.Deposit_Monthly_Activity "
        f"WHERE year_mount = {YM} GROUP BY customer_id", engine)
    sh, n, tot = top_shares(dep.set_index("customer_id").bal)
    print("deposit", n, tot / 1e13, sh)
    rows += [dict(basis="سپرده", top_pct=p, share_pct=v, customers=n, total_thousand_bn_toman=tot / 1e13) for p, v in sh.items()]
    pd.DataFrame(rows).to_csv(OUT / "concentration_primary_borrower.csv", index=False, encoding="utf-8-sig")

    # نقاط منحنی تمرکز (۴۰۰ نقطه) برای نمودار فصل ۴
    pts = []
    for name, ser in (("سپرده", dep.set_index("customer_id").bal), ("تسهیلات (گیرنده‌ی اصلی)", per_main)):
        s = np.sort(ser[ser > 0].to_numpy())[::-1]
        cum = np.cumsum(s) / s.sum()
        idx = np.unique(np.concatenate([np.logspace(0, np.log10(len(s)), 800).astype(int) - 1, np.arange(0, len(s), max(1, len(s) // 400))]))
        idx = idx[(idx >= 0) & (idx < len(s))]
        pts += [dict(basis=name, cust_share=(i + 1) / len(s), bal_share=cum[i]) for i in idx]
    pd.DataFrame(pts).to_csv(OUT / "concentration_lorenz_points.csv", index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
