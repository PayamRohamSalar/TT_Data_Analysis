"""آمار تجمیعی کل بانک از دو فایل تحویلی بانک (مانده‌ی سپرده‌ها و تسهیلات پرداختی): جدول‌ها و نمودارهای گزارش فاز ۱ (v9).

ورودی: data/سپرده های مانده دار.xlsx و data/تسهیلات پرداختی Sme.xlsx (بدون نیاز به DB)
خروجی: CSVهای data/processed/phase1_market_overview/bank_agg_*.csv و دو نمودار در reports/figures/phase1_market_overview
اجرا: python -u notebooks/phase1_market_overview/29_bank_aggregate_files.py
"""

import importlib.util
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("fig22", ROOT / "notebooks" / "phase1_market_overview" / "22_report_ch4_ch6_figures.py")
f22 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f22)
fd, save, pct0, BLUE, ORANGE, GREEN, GREY, LIGHT, RED = (f22.fd, f22.save, f22.pct0, f22.BLUE, f22.ORANGE, f22.GREEN,
                                                         f22.GREY, f22.LIGHT, f22.RED)
OUT = ROOT / "data" / "processed" / "phase1_market_overview"
DATA = ROOT / "data"
T = 1e13  # ریال به هزار میلیارد تومان


def norm(s):
    return s.replace("ي", "ی").replace("ك", "ک").strip() if isinstance(s, str) else s


def load_deposits():
    f = DATA / "سپرده های مانده دار.xlsx"
    parts = []
    for sh in pd.ExcelFile(f).sheet_names:
        d = pd.read_excel(f, sheet_name=sh, header=1)
        d.columns = ["level", "kind", "member", "count", "bal"]
        d[["level", "kind"]] = d[["level", "kind"]].ffill()
        d = d.dropna(subset=["count"]).copy()
        d["kind"] = d.kind.map(norm)
        d["member"] = d.member.map(norm)
        d["code"] = d.level.str.extract(r"^(\d+)")[0].astype(int)
        d["period"] = sh
        parts.append(d)
    return pd.concat(parts, ignore_index=True)


def load_loans():
    f = DATA / "تسهیلات پرداختی Sme.xlsx"
    parts = []
    for sh in pd.ExcelFile(f).sheet_names:
        d = pd.read_excel(f, sheet_name=sh, header=1)
        d.columns = ["grp", "size", "sector", "kind", "member", "n", "amt"]
        d[["grp", "size", "sector", "kind"]] = d[["grp", "size", "sector", "kind"]].ffill()
        d = d.dropna(subset=["n"]).copy()
        d["kind"] = d.kind.map(norm)
        d["member"] = d.member.map(norm)
        d["period"] = sh.replace("در سال ", "").replace("شش ماهه اول سال ", "H1_")
        parts.append(d)
    return pd.concat(parts, ignore_index=True)


# ---- سپرده
DEP = load_deposits()
BANDS = [("کمتر از ۱۰ میلیون", 101, 104), ("۱۰ تا ۱۰۰ میلیون", 105, 106), ("۱۰۰ میلیون تا ۱ میلیارد", 107, 113),
         ("۱ تا ۱۰ میلیارد", 114, 132), ("۱۰ تا ۱۰۰ میلیارد", 133, 141), ("بیش از ۱۰۰ میلیارد", 142, 148)]
# مرز طبقه‌ها (ریال): کد ۱۰۴ تا ۱۰۰ میلیون ریال، ۱۰۶ تا ۱ میلیارد ریال، ۱۱۳ تا ۱۰ میلیارد ریال، ۱۳۲ تا ۱۰۰ میلیارد ریال،
# ۱۴۱ تا ۱۰۰۰ میلیارد ریال؛ یعنی مرزهای تومانی ۱۰ میلیون، ۱۰۰ میلیون، ۱ میلیارد، ۱۰ میلیارد و ۱۰۰ میلیارد.


def dep_summary():
    rows = []
    for p, d in DEP.groupby("period"):
        tot_b, tot_n = d.bal.sum(), d["count"].sum()
        rows.append(dict(period=p, deposits=tot_n,
                         legal_share_bal=100 * d[d.kind == "حقوقی"].bal.sum() / tot_b,
                         legal_share_cnt=100 * d[d.kind == "حقوقی"]["count"].sum() / tot_n,
                         member_share_bal=100 * d[d.member == "تعاونی"].bal.sum() / tot_b,
                         member_share_cnt=100 * d[d.member == "تعاونی"]["count"].sum() / tot_n,
                         big1bn_share_bal=100 * d[d.code >= 114].bal.sum() / tot_b,
                         big1bn_share_cnt=100 * d[d.code >= 114]["count"].sum() / tot_n,
                         n_over100bn=int(d[d.code >= 142]["count"].sum()),
                         bal_over100bn_share=100 * d[d.code >= 142].bal.sum() / tot_b))
    return pd.DataFrame(rows)


def dep_composition(period="1404"):
    d = DEP[DEP.period == period]
    g = d.groupby(["kind", "member"])[["count", "bal"]].sum()
    g["share_cnt"] = 100 * g["count"] / g["count"].sum()
    g["share_bal"] = 100 * g.bal / g.bal.sum()
    g["avg_mt"] = g.bal / g["count"] / 1e7  # میلیون تومان
    return g.reset_index()


def dep_ladder(period="1404"):
    d = DEP[DEP.period == period]
    rows = []
    for name, lo, hi in BANDS:
        x = d[(d.code >= lo) & (d.code <= hi)]
        rows.append(dict(band=name, deposits=x["count"].sum(), share_cnt=100 * x["count"].sum() / d["count"].sum(),
                         share_bal=100 * x.bal.sum() / d.bal.sum()))
    return pd.DataFrame(rows)


# ---- تسهیلات
LN = load_loans()
SECT = ["صنعت", "خدمات", "مسکن", "بازرگانی", "کشاورزی"]
GRP = ["خرد", "کوچک", "متوسط", "بزرگ"]
PERIODS = ["1400", "1401", "1402", "1403", "1404", "H1_1405"]


def loan_yearly():
    rows = []
    for p in PERIODS:
        d = LN[LN.period == p]
        rows.append(dict(period=p, files=d.n.sum(), amt=d.amt.sum() / T, avg_mt=d.amt.sum() / d.n.sum() / 1e7,
                         legal_share_amt=100 * d[d.kind == "حقوقی"].amt.sum() / d.amt.sum(),
                         legal_share_files=100 * d[d.kind == "حقوقی"].n.sum() / d.n.sum(),
                         member_share_amt=100 * d[d.member == "تعاونی"].amt.sum() / d.amt.sum(),
                         member_share_files=100 * d[d.member == "تعاونی"].n.sum() / d.n.sum()))
    r = pd.DataFrame(rows)
    r["growth"] = r.amt.pct_change() * 100
    r.loc[r.period == "H1_1405", "growth"] = np.nan
    return r


def loan_sector():
    t = pd.DataFrame({p: LN[LN.period == p].groupby("sector").amt.sum() / T for p in PERIODS}).loc[SECT]
    return t


def loan_groups(period="1404"):
    d = LN[LN.period == period]
    g = d.groupby("grp")[["n", "amt"]].sum().loc[GRP]
    g["share_files"] = 100 * g.n / g.n.sum()
    g["share_amt"] = 100 * g.amt / g.amt.sum()
    g["avg_mt"] = g.amt / g.n / 1e7
    g["amt_h"] = g.amt / T
    return g.reset_index()


# ---- نمودارها
def fig_deposit_ladder():
    d = dep_ladder("1404")
    labels = ["کمتر از ۱۰\nمیلیون", "۱۰ تا ۱۰۰\nمیلیون", "۱۰۰ میلیون\nتا ۱ میلیارد", "۱ تا ۱۰\nمیلیارد",
              "۱۰ تا ۱۰۰\nمیلیارد", "بیش از ۱۰۰\nمیلیارد"]
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(11, 4.8))
    b1 = ax.bar(x - 0.2, d.share_cnt, 0.38, color=BLUE, label="سهم از تعداد سپرده‌ها")
    b2 = ax.bar(x + 0.2, d.share_bal, 0.38, color=ORANGE, label="سهم از مانده")
    for b in list(b1) + list(b2):
        h = b.get_height()
        txt = fd(f"{h:.1f}") if h >= 0.1 else (fd(f"{h:.2f}") if h >= 0.01 else "کمتر از " + fd("0.01"))
        ax.text(b.get_x() + b.get_width() / 2, h + 1, txt, ha="center", fontsize=9.5)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.yaxis.set_major_formatter(f22.FuncFormatter(pct0))
    ax.set_ylabel("سهم (درصد)")
    ax.set_xlabel("بازه‌ی مانده‌ی هر سپرده (تومان)")
    ax.legend(frameon=False, loc="upper right")
    ax.grid(axis="x", visible=False)
    save(fig, "ch4_bank_deposit_ladder.png")


def fig_loan_sector():
    t = loan_sector()
    cols = [BLUE, ORANGE, GREEN, GREY, LIGHT]
    labels = ["۱۴۰۰", "۱۴۰۱", "۱۴۰۲", "۱۴۰۳", "۱۴۰۴", "شش ماه اول\n۱۴۰۵"]
    fig, ax = plt.subplots(figsize=(10, 4.8))
    x = np.arange(len(PERIODS))
    bottom = np.zeros(len(PERIODS))
    for s, c in zip(SECT, cols):
        v = t.loc[s].values
        ax.bar(x, v, 0.6, bottom=bottom, color=c, label=s.replace("صنعت", "صنعت").replace("مسکن", "مسکن"))
        bottom += v
    for xi, tot in zip(x, bottom):
        ax.text(xi, tot + 1.5, fd(f"{tot:.1f}"), ha="center", fontsize=10)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10.5)
    ax.set_ylabel("مبلغ تسهیلات پرداختی (هزار میلیارد تومان)")
    ax.yaxis.set_major_formatter(f22.FuncFormatter(f22.fmt0))
    ax.set_ylim(0, bottom.max() * 1.12)
    ax.legend(frameon=False, loc="upper left", ncol=5, fontsize=10)
    ax.grid(axis="x", visible=False)
    save(fig, "ch5_bank_loan_disbursed_sector.png")


if __name__ == "__main__":
    dep_summary().to_csv(OUT / "bank_agg_deposit_trend.csv", index=False, encoding="utf-8-sig")
    dep_composition("1404").to_csv(OUT / "bank_agg_deposit_composition_1404.csv", index=False, encoding="utf-8-sig")
    dep_ladder("1404").to_csv(OUT / "bank_agg_deposit_ladder_1404.csv", index=False, encoding="utf-8-sig")
    loan_yearly().to_csv(OUT / "bank_agg_loan_yearly.csv", index=False, encoding="utf-8-sig")
    loan_sector().to_csv(OUT / "bank_agg_loan_sector.csv", encoding="utf-8-sig")
    loan_groups("1404").to_csv(OUT / "bank_agg_loan_groups_1404.csv", index=False, encoding="utf-8-sig")
    pd.set_option("display.width", 220, "display.max_columns", 30)
    print(dep_summary().round(2))
    print(dep_composition().round(2))
    print(dep_ladder().round(3))
    print(loan_yearly().round(2))
    print(loan_sector().round(2))
    print((loan_sector() / loan_sector().sum() * 100).round(1))
    print(loan_groups().round(2))
    print(loan_groups("1400").round(2))
    fig_deposit_ladder()
    fig_loan_sector()
