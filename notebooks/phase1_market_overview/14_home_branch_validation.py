"""
اعتبارسنجی «شعبه‌ی اصلی رابطه»ی مشتری در برابر گزارش‌های رسمی ماهانه‌ی بانک.

منبع مرجع: خروجی‌های گام ۱ (بانک در سطح کل و شعبه).
داده‌ی نمونه: از دیتابیس استخراج می‌شود.
"""

import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from tt_bank.common.persian_plot import fa, setup_persian_font, to_persian_digits
from tt_bank.db.connection import get_engine

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "phase1_market_overview"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures" / "phase1_market_overview"
DETAIL_MONTHS = (140205, 140212)
setup_persian_font()


def load_bank_reports() -> tuple[pd.DataFrame, pd.DataFrame]:
    bank_monthly = pd.read_csv(PROCESSED_DIR / "bank_official_monthly.csv")
    bank_branches = pd.read_csv(PROCESSED_DIR / "bank_official_monthly_by_branch.csv")
    return bank_branches, bank_monthly


def load_sample(engine, months: list[int]) -> tuple[pd.DataFrame, pd.DataFrame]:
    month_list = ",".join(str(m) for m in months)
    deposits = pd.read_sql(f"""
        WITH IA AS (
            SELECT CAST(REPLACE(REPLACE(LTRIM(RTRIM(Depositid)),CHAR(13),''),CHAR(10),'') AS numeric(38,0)) AS dep,
                   MIN(REPLACE(REPLACE(LTRIM(RTRIM(BranchCode)),CHAR(13),''),CHAR(10),''))                AS br
            FROM dbo.DepositIDInterest
            GROUP BY CAST(REPLACE(REPLACE(LTRIM(RTRIM(Depositid)),CHAR(13),''),CHAR(10),'') AS numeric(38,0))
        )
        SELECT CAST(d.year_mount AS bigint) AS year_month,
               COALESCE(ia.br, h.branch_code, 'NONE') AS br,
               CASE WHEN ia.br IS NOT NULL THEN 'account' WHEN h.branch_code IS NOT NULL THEN 'customer' ELSE 'none' END AS how,
               SUM(CAST(d.avr_total_amount_eq AS float)) AS balance
        FROM dbo.Deposit_Monthly_Activity d
        LEFT JOIN IA ia ON ia.dep = d.deposit_id
        LEFT JOIN dbo.Dim_Customer_Home_Branch h ON h.customer_id = d.customer_id
        WHERE CAST(d.year_mount AS bigint) IN ({month_list})
        GROUP BY CAST(d.year_mount AS bigint), COALESCE(ia.br, h.branch_code, 'NONE'),
                 CASE WHEN ia.br IS NOT NULL THEN 'account' WHEN h.branch_code IS NOT NULL THEN 'customer' ELSE 'none' END
    """, engine)
    
    loans = pd.read_sql(f"""
        WITH LB AS (
            SELECT loanfile_id, CAST(Transaction_Date AS bigint) / 100 AS year_month,
                   MAX(CAST(Total_Remain AS float)) AS balance,
                   MAX(CAST(Total_Remain AS float) - CAST(MANDE_JARI AS float)) AS npl
            FROM dbo.Loan_Remain
            WHERE CAST(Transaction_Date AS bigint) / 100 IN ({month_list})
            GROUP BY loanfile_id, CAST(Transaction_Date AS bigint) / 100
        )
        SELECT lb.year_month, COALESCE(m.branch_code, 'NONE') AS br, SUM(lb.balance) AS balance, SUM(lb.npl) AS npl
        FROM LB lb LEFT JOIN dbo.vw_Loan_Branch_Map m ON m.loanfile_id = lb.loanfile_id
        GROUP BY lb.year_month, COALESCE(m.branch_code, 'NONE')
    """, engine)
    
    for df in (deposits, loans):
        df["br"] = df["br"].astype(str).str.strip()
    return deposits, loans


def compare(ours: pd.Series, bank: pd.Series) -> dict:
    joined = pd.concat([ours.rename("ours"), bank.rename("bank")], axis=1).fillna(0)
    both = joined[(joined["ours"] > 0) & (joined["bank"] > 0)]
    shares = joined / joined.sum()
    return {
        "units_bank": int((joined["bank"] > 0).sum()),
        "units_both": len(both),
        "pearson_log": float(np.corrcoef(np.log(both["ours"]), np.log(both["bank"]))[0, 1]) if len(both) > 2 else np.nan,
        "spearman": float(both["ours"].rank().corr(both["bank"].rank())) if len(both) > 2 else np.nan,
        "share_similarity": float(1 - (shares["ours"] - shares["bank"]).abs().sum() / 2),
    }


def branch_series(frame: pd.DataFrame, value: str) -> pd.Series:
    s = frame[frame["br"] != "NONE"].groupby("br")[value].sum()
    s.index = pd.to_numeric(s.index, errors="coerce")
    return s[s.index.notna()].rename(index=int)


def validate(bank_branches: pd.DataFrame, bank_monthly: pd.DataFrame, deposits: pd.DataFrame, loans: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[int, pd.DataFrame]]:
    rows, details = [], {}
    coverage_rows = []
    
    for month, bm_row in bank_monthly.iterrows():
        ym = int(bm_row["year_month"])
        bank = bank_branches[bank_branches["year_month"] == ym]
        bank_by_code = bank.groupby("branch_code")
        prov_of = bank.drop_duplicates("branch_code").set_index("branch_code")["province"]
        bank_prov = bank.groupby("province")[["rial_resources", "loans"]].sum()

        dep_m = deposits[deposits["year_month"] == ym]
        sample_dep_total = dep_m["balance"].sum() if not dep_m.empty else 0
        
        if not dep_m.empty:
            for variant, subset in (("deposit_inferred", dep_m[dep_m["how"] != "none"]), ("deposit_account_only", dep_m[dep_m["how"] == "account"])):
                ours = branch_series(subset, "balance")
                bank_dep = bank_by_code["rial_resources"].sum()
                row = {"year_month": ym, "measure": variant, "level": "branch",
                       "bank_total": bank_dep.sum(), "sample_total": dep_m["balance"].sum(), "sample_assigned": ours.sum()}
                rows.append({**row, **compare(ours, bank_dep)})
                ours_prov = ours.groupby(ours.index.map(prov_of)).sum()
                rows.append({**row, "level": "province", **compare(ours_prov, bank_prov["rial_resources"])})
                if variant == "deposit_inferred" and ym in DETAIL_MONTHS:
                    details[ym] = pd.concat([bank.drop_duplicates("branch_code").set_index("branch_code")[["province", "rial_resources", "loans"]],
                                                ours.rename("sample_deposit")], axis=1)

        loan_m = loans[loans["year_month"] == ym]
        sample_loan_total = loan_m["balance"].sum() if not loan_m.empty else 0
        sample_npl_total = loan_m["npl"].sum() if not loan_m.empty else 0
        
        if not loan_m.empty:
            ours = branch_series(loan_m, "balance")
            bank_loan = bank_by_code["loans"].sum()
            row = {"year_month": ym, "measure": "loan_direct", "level": "branch",
                   "bank_total": bank_loan.sum(), "sample_total": loan_m["balance"].sum(), "sample_assigned": ours.sum()}
            rows.append({**row, **compare(ours, bank_loan)})
            ours_prov = ours.groupby(ours.index.map(prov_of)).sum()
            rows.append({**row, "level": "province", **compare(ours_prov, bank_prov["loans"])})
            if ym in details:
                details[ym]["sample_loan"] = ours
                
        # Calculate coverage row
        b_res = bm_row["rial_resources"]
        b_loan = bm_row["loans"]
        b_npl = bm_row["npl"]
        
        rel_dep = bool(bm_row["rial_resources_pure"])
        rel_npl = bool(bm_row["npl_available"])
        
        cov_dep = (sample_dep_total / b_res * 100) if (b_res and rel_dep) else np.nan
        cov_loan = (sample_loan_total / b_loan * 100) if b_loan else 0
        cov_npl = (sample_npl_total / b_npl * 100) if (pd.notna(b_npl) and b_npl and rel_npl) else np.nan
        
        coverage_rows.append({
            "year_month": ym,
            "bank_rial_resources": b_res,
            "sample_rial_resources": sample_dep_total,
            "deposit_coverage_pct": cov_dep,
            "bank_loans": b_loan,
            "sample_loans": sample_loan_total,
            "loan_coverage_pct": cov_loan,
            "bank_npl": b_npl,
            "sample_npl": sample_npl_total,
            "npl_coverage_pct": cov_npl,
            "deposit_coverage_reliable": rel_dep,
            "npl_coverage_reliable": rel_npl
        })

    result = pd.DataFrame(rows)
    result["coverage_pct"] = result["sample_total"] / result["bank_total"] * 100
    result["assigned_share_pct"] = result["sample_assigned"] / result["sample_total"] * 100
    
    coverage_df = pd.DataFrame(coverage_rows)
    return result, coverage_df, details


def plot(result: pd.DataFrame, details: dict[int, pd.DataFrame]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    ax = axes[0]
    styles = {("deposit_inferred", "branch"): ("سپرده — استنتاج شعبه‌ی مشتری", "tab:blue", "-"),
              ("deposit_account_only", "branch"): ("سپرده — فقط حساب سوددار", "tab:blue", ":"),
              ("loan_direct", "branch"): ("تسهیلات — شعبه‌ی قرارداد", "tab:orange", "-"),
              ("deposit_inferred", "province"): ("سپرده — سطح استان", "tab:green", "--")}
    all_months = sorted(result["year_month"].unique())
    position = {m: i for i, m in enumerate(all_months)}
    for (measure, level), (label, color, ls) in styles.items():
        s = result[(result["measure"] == measure) & (result["level"] == level)].sort_values("year_month")
        if not s.empty:
            ax.plot(s["year_month"].map(position), s["share_similarity"] * 100, color=color, linestyle=ls, label=fa(label), linewidth=2)
    ticks = list(range(0, len(all_months), max(1, len(all_months) // 8)))
    ax.set_xticks(ticks)
    ax.set_xticklabels([to_persian_digits(f"{all_months[i] // 100}/{all_months[i] % 100:02d}") for i in ticks], rotation=30, fontsize=8)
    ax.set_ylim(0, 100)
    ax.set_ylabel(fa("شباهت سهم‌ها با گزارش رسمی بانک (درصد)"))
    ax.set_title(fa("هم‌خوانی توزیع شعبه‌ای نمونه با گزارش ماهانه‌ی بانک"))
    ax.yaxis.set_major_formatter(lambda v, pos: to_persian_digits(f"{v:.0f}"))
    ax.legend(fontsize=8)

    ax = axes[1]
    if details:
        month = max(details)
        d = details[month].dropna(subset=["rial_resources", "sample_deposit"])
        d = d[(d["rial_resources"] > 0) & (d["sample_deposit"] > 0)]
        ax.scatter(d["rial_resources"] / 1e12, d["sample_deposit"] / 1e12, s=10, alpha=0.6)
        lim = [min(d["rial_resources"].min(), d["sample_deposit"].min()) / 1e12, max(d["rial_resources"].max(), d["sample_deposit"].max()) / 1e12]
        ax.plot(lim, lim, color="grey", linewidth=1, linestyle="--")
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlabel(fa("مانده‌ی سپرده‌ی شعبه در گزارش رسمی بانک (هزار میلیارد ریال)"))
        ax.set_ylabel(fa("مانده‌ی سپرده‌ی نسبت‌داده‌شده در نمونه (هزار میلیارد ریال)"))
        ax.set_title(fa(f"مقایسه‌ی شعبه‌به‌شعبه — {to_persian_digits(f'{month // 100}/{month % 100:02d}')}"))
    
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "home_branch_validation.png", dpi=150)
    plt.close(fig)


def main() -> None:
    engine = get_engine()
    bank_branches, bank_monthly = load_bank_reports()
    months = sorted(bank_monthly["year_month"].unique())
    deposits, loans = load_sample(engine, months)
    engine.dispose()
    
    result, coverage_df, details = validate(bank_branches, bank_monthly, deposits, loans)

    result.to_csv(PROCESSED_DIR / "home_branch_validation_monthly.csv", index=False)
    coverage_df.to_csv(PROCESSED_DIR / "bank_coverage_monthly.csv", index=False)
    
    plot(result, details)

    # Output validations for prompt checks
    print("--- معیارهای تحویل ---")
    print(f"1. ردیف‌های bank_coverage_monthly: {len(coverage_df)} (مورد انتظار: 60 بدون شکاف)")
    
    c_140412 = coverage_df[coverage_df["year_month"] == 140412].iloc[0]
    print(f"2. پوشش 140412: سپرده {c_140412['deposit_coverage_pct']:.1f}%، تسهیلات {c_140412['loan_coverage_pct']:.1f}%، NPL {c_140412['npl_coverage_pct']:.1f}%")
    
    for m in [140012, 140111]:
        c = coverage_df[coverage_df["year_month"] == m].iloc[0]
        print(f"3. بررسی {m}: deposit_reliable={c['deposit_coverage_reliable']}, npl_reliable={c['npl_coverage_reliable']} | loan_coverage={c['loan_coverage_pct']:.1f}%")
        
    for m in [140312, 140412]:
        b = bank_monthly[bank_monthly["year_month"] == m].iloc[0]
        ratio = b['npl'] / b['loans'] * 100
        print(f"4. نسبت مطالبات رسمی {m}: {ratio:.2f}%")


if __name__ == "__main__":
    main()
