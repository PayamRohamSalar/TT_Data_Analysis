"""
تعیین «شعبه‌ی اصلی رابطه»ی هر مشتری — پیش‌نیاز تحلیل تراکنش به تفکیک شعبه/استان (فاز ۱، فصل ۶) و
دسته‌بندی مشتریان (فاز ۲).

مسئله: تنها ستون شعبه‌ی سطح-مشتری (`Customer_Profile.creator_branch`) به جداول عملیاتی وصل نمی‌شود
(فضای شناسه‌ی متفاوت — docs/05) و هیچ‌یک از جداول سپرده و گردش (`Deposit_Accoutnt_Info`,
`Deposit_Monthly_Activity`, `Customer_Monthly_Activity`) ستون شعبه ندارند. شماره‌ی حساب هم کد شعبه را
در خود ندارد (`DEPOSIT_ID` = `DEPOSIT_ID_KEY`، ناشناس‌سازی‌شده؛ آزمون ۲۰۲۶-۰۹-۱۴: تطابق ۰.۰٪).

راه‌حل: شعبه‌ی غالب هر مشتری از سه مسیر غیرمستقیم، به ترتیب اولویت:
  A — حساب‌های سوددار: `DepositIDInterest.BranchCode` (هر حساب دقیقاً یک شعبه؛ وزن = مجموع سود پرداختی)
  B — وام‌گیرنده‌ی اصلی: `vw_Loan_Contract_Dedup` × `LoanFileID_Brnach` (وزن = مبلغ اعطا)
  C — همه‌ی طرفین قرارداد (شامل ضامن): `Loan_Remain.customer_id` × `LoanFileID_Brnach` (وزن = مانده + ۱)

نتیجه‌ی آزمون (۲۰۲۶-۰۹-۱۴): ۸۴.۴٪ سپرده‌گذاران، ۹۱.۰٪ مانده، ۹۰.۵٪ گردش سپرده، ۴۴۹ شعبه.
اعتبار: دو مسیر مستقل A و B برای ۸۴.۴٪ مشتریان مشترک، همان شعبه (۸۹.۸٪ همان شهر) را می‌دهند.

⚠️ معنای درست: «شعبه‌ی اصلی رابطه»، نه شعبه‌ی افتتاح حساب. مشتریان بدون شعبه (~۱۵.۶٪) عمدتاً
دارندگان صرف حساب جاری/قرض‌الحسنه‌اند که نه وام دارند نه حساب سوددار — در تحلیل جغرافیایی کم‌نمایش‌اند.
برای حساب‌های سوددار، شعبه‌ی خودِ حساب (مسیر A در سطح حساب) از شعبه‌ی غالب مشتری دقیق‌تر است؛ اسکریپت ۱۴
در سطح حساب از COALESCE(شعبه‌ی حساب، شعبه‌ی مشتری) استفاده می‌کند.

خروجی:
  - جدول دیتابیس `dbo.Dim_Customer_Home_Branch` (یک ردیف به‌ازای هر مشتری دارای شعبه)
  - data/processed/phase1_market_overview/customer_home_branch.csv
  - data/processed/phase1_market_overview/customer_home_branch_coverage.csv
"""

import time
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.types import CHAR, DECIMAL, INTEGER, NVARCHAR, VARCHAR, Float

from tt_bank.db.connection import get_engine

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "phase1_market_overview"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
DIM_TABLE = "Dim_Customer_Home_Branch"


def read(engine, label: str, sql: str) -> pd.DataFrame:
    start = time.time()
    df = pd.read_sql(sql, engine)
    print(f"[{label}] {len(df):,} ردیف، {time.time() - start:.0f} ثانیه", flush=True)
    return df


def to_id(series: pd.Series) -> pd.Series:
    """شناسه‌های عددی (numeric/varchar) را به رشته‌ی عدد صحیح یکسان تبدیل می‌کند تا join بین جداول درست شود."""
    return pd.to_numeric(series, errors="coerce").astype("Int64").astype(str)


def dominant_branch(customer_branch_weight: pd.DataFrame, route: str) -> pd.DataFrame:
    """برای هر مشتری: شعبه‌ی با بیشترین وزن، تعداد شعب متمایز، و سهم وزن شعبه‌ی غالب."""
    cbw = customer_branch_weight.sort_values(["cid", "w"], ascending=[True, False])
    top = cbw.drop_duplicates("cid").set_index("cid")["br"].rename(f"branch_{route}")
    n_branches = cbw.groupby("cid")["br"].nunique().rename(f"n_branches_{route}")
    top_share = (cbw.drop_duplicates("cid").set_index("cid")["w"] / cbw.groupby("cid")["w"].sum()).rename(f"top_share_{route}")
    return pd.concat([top, n_branches, top_share], axis=1)


def load_routes(engine) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    account_customer = read(engine, "حساب → مشتری", "SELECT DISTINCT deposit_id, customer_id FROM dbo.Deposit_Monthly_Activity")
    account_customer["dep"] = to_id(account_customer["deposit_id"])
    account_customer["cid"] = to_id(account_customer["customer_id"])

    interest = read(engine, "مسیر A: حساب سوددار → شعبه", """
        SELECT CAST(REPLACE(REPLACE(LTRIM(RTRIM(Depositid)),CHAR(13),''),CHAR(10),'') AS varchar(40)) AS dep,
               REPLACE(REPLACE(LTRIM(RTRIM(BranchCode)),CHAR(13),''),CHAR(10),'')               AS br,
               SUM(CAST(Amount AS float))                                                          AS w
        FROM dbo.DepositIDInterest
        GROUP BY CAST(REPLACE(REPLACE(LTRIM(RTRIM(Depositid)),CHAR(13),''),CHAR(10),'') AS varchar(40)),
                 REPLACE(REPLACE(LTRIM(RTRIM(BranchCode)),CHAR(13),''),CHAR(10),'')
    """)
    interest["dep"] = to_id(interest["dep"])
    route_a = interest.merge(account_customer[["dep", "cid"]], on="dep").groupby(["cid", "br"], as_index=False)["w"].sum()

    loan_branch = read(engine, "قرارداد → شعبه", "SELECT loanfile_id AS lf, branch_code AS br FROM dbo.vw_Loan_Branch_Map")
    loan_branch["lf"] = to_id(loan_branch["lf"])
    primary = read(engine, "مسیر B: قرارداد → وام‌گیرنده‌ی اصلی",
                   "SELECT loanfile_id AS lf, main_customer_id AS cid, CAST(grant_amount AS float) AS w FROM dbo.vw_Loan_Contract_Dedup")
    primary["lf"], primary["cid"] = to_id(primary["lf"]), to_id(primary["cid"])
    route_b = primary.merge(loan_branch, on="lf").groupby(["cid", "br"], as_index=False)["w"].sum()

    parties = read(engine, "مسیر C: قرارداد → همه‌ی طرفین", """
        SELECT loanfile_id AS lf, customer_id AS cid, MAX(CAST(Total_Remain AS float)) AS w
        FROM dbo.Loan_Remain GROUP BY loanfile_id, customer_id
    """)
    parties["lf"], parties["cid"] = to_id(parties["lf"]), to_id(parties["cid"])
    parties["w"] = parties["w"].fillna(0) + 1.0  # قرارداد تسویه‌شده هم شاهد رابطه است
    route_c = parties.merge(loan_branch, on="lf").groupby(["cid", "br"], as_index=False)["w"].sum()

    for df in (route_a, route_b, route_c):
        df["br"] = df["br"].astype(str).str.strip()
    return route_a, route_b, route_c


def build_assignment(engine) -> pd.DataFrame:
    route_a, route_b, route_c = load_routes(engine)
    home = dominant_branch(route_a, "A").join(dominant_branch(route_b, "B"), how="outer").join(dominant_branch(route_c, "C"), how="outer")
    home["branch_code"] = home["branch_A"].fillna(home["branch_B"]).fillna(home["branch_C"])
    home["source"] = np.select([home["branch_A"].notna(), home["branch_B"].notna()], ["A", "B"], "C")

    city = read(engine, "شعبه → شهر", "SELECT DISTINCT branch_code, city_name FROM dbo.vw_Branch_Dim")
    city = city.assign(branch_code=city["branch_code"].astype(str).str.strip()).drop_duplicates("branch_code")
    home = home.reset_index().rename(columns={"cid": "customer_id"}).merge(city, on="branch_code", how="left")
    home = home[home["customer_id"] != "<NA>"]

    both = home.dropna(subset=["branch_A", "branch_B"])
    city_map = city.set_index("branch_code")["city_name"]
    print(f"\nاعتبار: توافق شعبه‌ی غالب در دو مسیر مستقل A و B روی {len(both):,} مشتری مشترک = "
          f"{(both['branch_A'] == both['branch_B']).mean() * 100:.1f}٪ (همان شهر: "
          f"{(both['branch_A'].map(city_map) == both['branch_B'].map(city_map)).mean() * 100:.1f}٪)")
    return home


def coverage_summary(engine, home: pd.DataFrame) -> pd.DataFrame:
    customers = read(engine, "جامعه‌ی سپرده‌گذاران: مانده و گردش", """
        SELECT customer_id,
               SUM(CAST(sum_creditor_circul_amount_eq AS float) + CAST(sum_debtor_circul_amount_eq AS float)) AS turnover_all,
               SUM(CASE WHEN CAST(year_mount AS bigint) BETWEEN 140401 AND 140412
                        THEN CAST(sum_creditor_circul_amount_eq AS float) + CAST(sum_debtor_circul_amount_eq AS float) ELSE 0 END) AS turnover_1404,
               SUM(CASE WHEN CAST(year_mount AS bigint) = 140412 THEN CAST(avr_total_amount_eq AS float) ELSE 0 END) AS balance_140412
        FROM dbo.Deposit_Monthly_Activity GROUP BY customer_id
    """)
    customers["customer_id"] = to_id(customers["customer_id"])
    u = customers.merge(home[["customer_id", "source"]], on="customer_id", how="left")
    u["source"] = u["source"].fillna("بدون شعبه")

    rows, cumulative = [], pd.Series(False, index=u.index)
    for label, mask in (("A: حساب سوددار", u["source"] == "A"),
                        ("A+B: + وام‌گیرنده‌ی اصلی", u["source"] == "B"),
                        ("A+B+C: + ضامن/شریک", u["source"] == "C"),
                        ("بدون شعبه", u["source"] == "بدون شعبه")):
        if label == "بدون شعبه":
            selected = mask
        else:
            cumulative = cumulative | mask
            selected = cumulative
        rows.append({
            "route": label,
            "customers": int(selected.sum()),
            "customer_share_pct": selected.mean() * 100,
            "balance_share_pct": u.loc[selected, "balance_140412"].sum() / u["balance_140412"].sum() * 100,
            "turnover_all_share_pct": u.loc[selected, "turnover_all"].sum() / u["turnover_all"].sum() * 100,
            "turnover_1404_share_pct": u.loc[selected, "turnover_1404"].sum() / u["turnover_1404"].sum() * 100,
        })
    summary = pd.DataFrame(rows)
    print("\n=== پوشش روی کل سپرده‌گذاران ===")
    print(summary.round(1).to_string(index=False))
    return summary


def materialize(engine, home: pd.DataFrame) -> None:
    """جدول را در دیتابیس می‌نویسد تا اسکریپت ۱۴ و تحلیل‌های فاز ۲ مستقیم در SQL join کنند.
    ⚠️ از همان engine اسکریپت استفاده می‌کند (نه یک engine دوم): اگر سرور در حالت تک‌کاربره (-m) باشد، اتصال دوم
    رد می‌شود — این دقیقاً در اجرای اول ۲۰۲۶-۰۹-۱۴ رخ داد."""
    table = home[["customer_id", "branch_code", "source", "city_name",
                  "branch_A", "branch_B", "branch_C", "n_branches_A", "n_branches_B", "n_branches_C",
                  "top_share_A", "top_share_B"]].copy()
    table["customer_id"] = pd.to_numeric(table["customer_id"])
    for col in ("n_branches_A", "n_branches_B", "n_branches_C"):
        table[col] = table[col].astype("Int64")
    start = time.time()
    table.to_sql(DIM_TABLE, engine, schema="dbo", if_exists="replace", index=False, chunksize=50_000, dtype={
        "customer_id": DECIMAL(38, 0), "branch_code": VARCHAR(10), "source": CHAR(1), "city_name": NVARCHAR(100),
        "branch_A": VARCHAR(10), "branch_B": VARCHAR(10), "branch_C": VARCHAR(10),
        "n_branches_A": INTEGER(), "n_branches_B": INTEGER(), "n_branches_C": INTEGER(),
        "top_share_A": Float(), "top_share_B": Float(),
    })
    with engine.begin() as conn:
        conn.execute(text(f"CREATE UNIQUE CLUSTERED INDEX IX_{DIM_TABLE}_customer ON dbo.{DIM_TABLE}(customer_id)"))
    print(f"\nجدول dbo.{DIM_TABLE} با {len(table):,} ردیف ساخته شد ({time.time() - start:.0f} ثانیه).")


def main() -> None:
    engine = create_engine(get_engine().url, fast_executemany=True)  # یک engine برای خواندن و نوشتن
    home = build_assignment(engine)
    summary = coverage_summary(engine, home)
    home.to_csv(PROCESSED_DIR / "customer_home_branch.csv", index=False)
    summary.to_csv(PROCESSED_DIR / "customer_home_branch_coverage.csv", index=False)
    materialize(engine, home)
    print(f"شعب پوشش‌داده‌شده: {home['branch_code'].nunique():,}")


if __name__ == "__main__":
    main()
