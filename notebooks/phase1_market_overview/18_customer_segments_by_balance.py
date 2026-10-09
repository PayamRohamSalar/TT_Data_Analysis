"""توزیع مشتریان سپرده‌گذار در طبقات مانده‌ی سپرده (۱۲/۱۴۰۴) به تفکیک رابطه‌ی اعتباری.

گروه‌ها: «فقط سپرده‌گذار» و «سپرده‌گذار و گیرنده‌ی اصلی تسهیلات» (Loan_Grant_Customer).
خروجی: data/processed/phase1_market_overview/deposit_balance_by_relationship.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd

from tt_bank.db.connection import get_engine

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "processed" / "phase1_market_overview"


def main() -> None:
    engine = get_engine()
    primary = set(pd.read_sql("SELECT DISTINCT ID FROM dbo.Loan_Grant_Customer", engine)["ID"])
    depositors = pd.read_sql(
        "SELECT DISTINCT CAST(LTRIM(RTRIM(MAIN_CUSTOMER_ID)) AS numeric(38,0)) AS customer_id FROM dbo.Deposit_Accoutnt_Info "
        "WHERE ISNUMERIC(LTRIM(RTRIM(MAIN_CUSTOMER_ID))) = 1", engine)
    bal = pd.read_sql(
        "SELECT customer_id, SUM(avr_total_amount_eq) AS bal FROM dbo.Deposit_Monthly_Activity WHERE year_mount = 140412 GROUP BY customer_id",
        engine)
    d = depositors.merge(bal, on="customer_id", how="left")
    d["bal"] = d["bal"].fillna(0.0)
    d["has_loan"] = d.customer_id.isin(primary)
    print("depositors", len(d), "with loan", int(d.has_loan.sum()), "no-balance-record", int((d.bal == 0).sum()), flush=True)

    edges = [-np.inf, 5e6, 2.5e7, 1e8, 5e8, 2e9, 1e10, np.inf]
    labels = ["کمتر از ۰.۵ میلیون تومان", "۰.۵ تا ۲.۵ میلیون", "۲.۵ تا ۱۰ میلیون", "۱۰ تا ۵۰ میلیون",
              "۵۰ تا ۲۰۰ میلیون", "۲۰۰ میلیون تا ۱ میلیارد", "بیش از ۱ میلیارد"]
    d["band"] = pd.cut(d.bal, edges, right=False, labels=labels)
    rows = []
    for name, sub in (("فقط سپرده‌گذار", d[~d.has_loan]), ("سپرده‌گذار و گیرنده‌ی اصلی", d[d.has_loan])):
        g = sub.groupby("band", observed=False).agg(customers=("customer_id", "count"), balance=("bal", "sum")).reset_index()
        g.insert(0, "group", name)
        rows.append(g)
    res = pd.concat(rows)
    res["balance_thousand_bn_toman"] = res.balance / 10 / 1e12
    res.to_csv(OUT / "deposit_balance_by_relationship.csv", index=False, encoding="utf-8-sig")
    print(res.to_string(), flush=True)


if __name__ == "__main__":
    main()
