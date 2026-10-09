"""نمودارهای فصل‌های ۴ تا ۶ گزارش فاز ۱ (نسخه‌ی v4): فقط از CSVهای data/processed تولید می‌شوند.

همه‌ی مبالغ به هزار میلیارد تومان (همت)، تاریخ‌ها به صورت ماه/سال با ارقام فارسی، بدون واژه‌ی انگلیسی.
اجرا: python -u notebooks/phase1_market_overview/22_report_ch4_ch6_figures.py   (نیاز به DB ندارد)
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter

from tt_bank.common.persian_plot import FONTS_DIR, setup_persian_font, to_persian_digits

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "reports" / "figures" / "phase1_market_overview"
D = ROOT / "data" / "processed" / "phase1_market_overview"
T = 1e13  # ریال به هزار میلیارد تومان

setup_persian_font()
font_manager.fontManager.addfont(str(FONTS_DIR / "Vazirmatn-Bold.ttf"))
BLUE, ORANGE, GREEN, RED, GREY, LIGHT = "#1F4E79", "#C55A11", "#548235", "#B03A2E", "#7F7F7F", "#9DB7D5"
plt.rcParams.update({
    "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#888888",
    "axes.labelcolor": "#333333", "xtick.color": "#333333", "ytick.color": "#333333",
    "font.size": 11, "figure.dpi": 100, "savefig.dpi": 200, "axes.grid": True,
    "grid.color": "#E6E6E6", "grid.linewidth": 0.7, "axes.axisbelow": True,
})


def fd(x) -> str:
    return to_persian_digits(x)


def fmt1(v, _=None):
    return fd(f"{v:,.1f}")


def fmt0(v, _=None):
    return fd(f"{v:,.0f}")


def pct0(v, _=None):
    return fd(f"{v:.0f}") + "٪"


def ym_label(ym) -> str:
    s = str(int(ym))
    return fd(f"{s[4:6]}/{s[:4]}")


def persianize(fig):
    """ارقام لاتین تیک‌های محورها را فارسی می‌کند (فرمت‌کننده‌ی فعلی هر محور حفظ می‌شود)."""
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            f = axis.get_major_formatter()
            axis.set_major_formatter(FuncFormatter(lambda v, pos, f=f: fd(f(v, pos))))


def save(fig, name):
    persianize(fig)
    fig.savefig(FIG / name, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", name)


def time_axis(ax, yms, step=6):
    idx = list(range(0, len(yms), step))
    if len(yms) - 1 not in idx and (len(yms) - 1 - idx[-1]) >= step // 2:
        idx.append(len(yms) - 1)
    ax.set_xticks(idx)
    ax.set_xticklabels([ym_label(yms[i]) for i in idx], fontsize=10)


def hbar(ax, labels, vals, colors=None, fmt=fmt1, xlabel="", suffix="", pad=0.01):
    y = np.arange(len(labels))[::-1]
    ax.barh(y, vals, color=colors or BLUE, height=0.62)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=10.5)
    top = max(vals) if len(vals) else 1
    for yi, v in zip(y, vals):
        ax.text(v + top * pad, yi, fmt(v) + suffix, va="center", ha="left", fontsize=10)
    ax.set_xlim(0, top * 1.16)
    ax.set_xlabel(xlabel)
    ax.grid(axis="y", visible=False)


official = pd.read_csv(D / "bank_official_monthly.csv").sort_values("year_month")
official = official[official.year_month >= 140001].reset_index(drop=True)
official["res"] = official.rial_resources / T
official["loan"] = official.loans / T
official["ldr"] = 100 * official.loans / official.rial_resources


# ------------------------------------------------------------------ فصل ۴
def ch4_deposit_trend():
    s = pd.read_csv(D / "deposit_balance_trend_full.csv")
    s = s[s.year_mount >= 140001].reset_index(drop=True)
    yms = s.year_mount.astype(int).tolist()
    off = official.set_index("year_month").res.reindex(yms)
    fig, ax = plt.subplots(figsize=(11, 4.6))
    ax.plot(range(len(yms)), off.values, color=ORANGE, lw=2.2, label="منابع ریالی رسمی بانک")
    ax.plot(range(len(yms)), s.total_balance_estimate / T, color=BLUE, lw=2.2, label="مانده‌ی سپرده‌ی نمونه")
    time_axis(ax, yms)
    ax.yaxis.set_major_formatter(FuncFormatter(fmt0))
    ax.set_ylabel("هزار میلیارد تومان")
    ax.legend(frameon=False, loc="upper left")
    save(fig, "ch4_deposit_trend.png")


def ch4_yoy():
    yrs = [1401, 1402, 1403, 1404]
    y = pd.read_csv(D / "yoy_growth.csv").set_index("shamsi_year")
    o = official.copy()
    o["yr"] = o.year_month // 100
    end = o[o.year_month % 100 == 12].set_index("yr")
    og_res = [100 * (end.loc[v, "res"] / end.loc[v - 1, "res"] - 1) for v in yrs]
    og_loan = [100 * (end.loc[v, "loan"] / end.loc[v - 1, "loan"] - 1) for v in yrs]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), sharey=True)
    for ax, title, s_vals, o_vals in (
            (axes[0], "منابع ریالی", [y.loc[v, "deposit_yoy_pct"] for v in yrs], og_res),
            (axes[1], "تسهیلات", [y.loc[v, "loan_yoy_pct"] for v in yrs], og_loan)):
        x = np.arange(len(yrs))
        b1 = ax.bar(x - 0.2, o_vals, 0.38, color=ORANGE, label="آمار رسمی بانک")
        b2 = ax.bar(x + 0.2, s_vals, 0.38, color=BLUE, label="نمونه")
        for b in list(b1) + list(b2):
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.8, fd(f"{b.get_height():.1f}"), ha="center", fontsize=9.5)
        ax.set_xticks(x)
        ax.set_xticklabels([fd(v) for v in yrs])
        ax.set_title(title, fontsize=12.5, color=BLUE)
        ax.grid(axis="x", visible=False)
    axes[0].set_ylabel("رشد سالانه (درصد)")
    axes[0].yaxis.set_major_formatter(FuncFormatter(pct0))
    axes[0].set_ylim(0, 56)
    axes[1].legend(frameon=False, loc="upper left", ncol=2, fontsize=10)
    save(fig, "ch4_yoy_growth.png")


def ch4_composition():
    d = pd.read_csv(D / "deposit_portfolio_latest_month.csv")
    names = {"سرمایه گذاری بلند مدت": "سرمایه‌گذاری بلندمدت", "پس انداز جاری": "پس‌انداز جاری",
             "سرمایه گذاری کوتاه مدت": "سرمایه‌گذاری کوتاه‌مدت", "قرض الحسنه پس انداز": "قرض‌الحسنه پس‌انداز",
             "ویژه": "ویژه", "سرمایه گذاری کوتاه مدت ویژه": "کوتاه‌مدت ویژه", "نامشخص": "نوع ثبت‌نشده"}
    d = d.sort_values("total_balance", ascending=False)
    labels = [names[v] for v in d.deposit_type]
    cols = [GREY if v == "نامشخص" else BLUE for v in d.deposit_type]
    fig, ax = plt.subplots(figsize=(10, 4.6))
    hbar(ax, labels, d.total_balance / T, cols, xlabel="مانده (هزار میلیارد تومان)")
    save(fig, "ch4_deposit_composition.png")


def ch4_ladder():
    d = pd.read_csv(D / "deposit_balance_ladder.csv")
    labels = ["کمتر از ۰.۵\nمیلیون", "۰.۵ تا ۲.۵\nمیلیون", "۲.۵ تا ۱۰\nمیلیون", "۱۰ تا ۵۰\nمیلیون",
              "۵۰ تا ۲۰۰\nمیلیون", "۲۰۰ میلیون\nتا ۱ میلیارد", "بیش از ۱\nمیلیارد"]
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(11, 4.8))
    b1 = ax.bar(x - 0.2, d.customer_share_pct, 0.38, color=BLUE, label="سهم از تعداد مشتریان")
    b2 = ax.bar(x + 0.2, d.balance_share_pct, 0.38, color=ORANGE, label="سهم از مانده")
    for b in list(b1) + list(b2):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1, fd(f"{b.get_height():.1f}"), ha="center", fontsize=9.5)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.yaxis.set_major_formatter(FuncFormatter(pct0))
    ax.set_ylabel("سهم (درصد)")
    ax.set_xlabel("بازه‌ی مانده‌ی سپرده‌گذار (تومان)")
    ax.legend(frameon=False, loc="upper center")
    ax.grid(axis="x", visible=False)
    save(fig, "ch4_deposit_ladder.png")


def ch4_lorenz():
    p = pd.read_csv(D / "concentration_lorenz_points.csv")
    fig, ax = plt.subplots(figsize=(8.5, 6.4))
    for name, col, lab in (("سپرده", BLUE, "مانده‌ی سپرده"), ("تسهیلات (گیرنده‌ی اصلی)", ORANGE, "مانده‌ی تسهیلات (گیرنده‌ی اصلی)")):
        q = p[p.basis == name].sort_values("cust_share")
        ax.plot(100 * q.cust_share, 100 * q.bal_share, color=col, lw=2.4, label=lab)
    ax.plot([0, 100], [0, 100], color=GREY, ls="--", lw=1.2, label="توزیع کاملاً برابر")
    ax.set_xscale("symlog", linthresh=1)
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 1, 5, 10, 20, 50, 100])
    ax.set_xticklabels([fd(v) + "٪" for v in [0, 1, 5, 10, 20, 50, 100]])
    ax.yaxis.set_major_formatter(FuncFormatter(pct0))
    ax.set_xlabel("سهم تجمعی مشتریان (به ترتیب نزولی مانده، مقیاس لگاریتمی)")
    ax.set_ylabel("سهم تجمعی از مانده")
    for xv, yv, col in ((1, 78.2, BLUE), (1, 50.5, ORANGE)):
        ax.scatter([xv], [yv], color=col, zorder=5)
        ax.annotate(fd(f"{yv:.1f}") + "٪", (xv, yv), textcoords="offset points", xytext=(8, -4), fontsize=10, color=col)
    ax.legend(frameon=False, loc="lower right")
    save(fig, "ch4_concentration_lorenz.png")


# ------------------------------------------------------------------ فصل ۵
def ch5_ldr():
    s = pd.read_csv(D / "loan_to_deposit_ratio.csv")
    yms = s.year_mount.astype(int).tolist()
    off = official.set_index("year_month").ldr.reindex(yms)
    fig, ax = plt.subplots(figsize=(11, 4.6))
    ax.plot(range(len(yms)), off.values, color=ORANGE, lw=2.2, label="آمار رسمی بانک")
    ax.plot(range(len(yms)), s.ldr_pct, color=BLUE, lw=2.2, label="نمونه (اثر تفاوت پوشش)")
    time_axis(ax, yms)
    ax.yaxis.set_major_formatter(FuncFormatter(pct0))
    ax.set_ylabel("تسهیلات به منابع ریالی")
    ax.set_ylim(95, 160)
    ax.legend(frameon=False, loc="upper left")
    save(fig, "ch5_ldr_official_vs_sample.png")


def ch5_loan_type():
    d = pd.read_csv(D / "loan_type_distribution.csv").sort_values("total_balance", ascending=False)
    labels = ["فاقد رکورد قرارداد" if v.startswith("نامشخص") else v for v in d.loan_type_group]
    cols = [GREY if v.startswith("نامشخص") else BLUE for v in d.loan_type_group]
    fig, ax = plt.subplots(figsize=(10, 4.6))
    hbar(ax, labels, d.total_balance / T, cols, xlabel="مانده (هزار میلیارد تومان)")
    save(fig, "loan_type_distribution.png")


def ch5_sector():
    d = pd.read_csv(D / "receivables_by_sector_latest_month.csv").sort_values("total_balance", ascending=False)
    names = {"اعتباراسنادی": "اعتبارات اسنادی", "صنایع تبدیلی بخش کشاورزی": "صنایع تبدیلی کشاورزی"}
    d = d[d.economic_sector != "متفرقه"]
    labels = [names.get(v, v) for v in d.economic_sector]
    ratio = 100 * d.npl_balance / d.total_balance
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6), gridspec_kw={"width_ratios": [1.15, 1]})
    hbar(axes[0], labels, d.total_balance / T, BLUE, xlabel="مانده (هزار میلیارد تومان)")
    y = np.arange(len(labels))[::-1]
    cols = [RED if v > 50 else ORANGE for v in ratio]
    axes[1].barh(y, ratio, color=cols, height=0.62)
    for yi, v in zip(y, ratio):
        axes[1].text(v + 1.2, yi, fd(f"{v:.1f}") + "٪", va="center", fontsize=10)
    axes[1].set_yticks(y)
    axes[1].set_yticklabels([])
    axes[1].set_xlim(0, 100)
    axes[1].set_xlabel("نسبت مطالبات غیرجاری (درصد)")
    axes[1].grid(axis="y", visible=False)
    save(fig, "receivables_by_sector_latest.png")


def ch5_size():
    d = pd.read_csv(D / "loan_size_histogram.csv")
    labels = ["کمتر از ۵۰\nمیلیون", "۵۰ تا ۲۰۰\nمیلیون", "۲۰۰ میلیون\nتا ۱ میلیارد", "۱ تا ۵\nمیلیارد", "بیش از ۵\nمیلیارد"]
    cs = 100 * d.loan_count / d.loan_count.sum()
    ms = 100 * d.total_granted / d.total_granted.sum()
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(10.5, 4.6))
    b1 = ax.bar(x - 0.2, cs, 0.38, color=BLUE, label="سهم از تعداد قراردادها")
    b2 = ax.bar(x + 0.2, ms, 0.38, color=ORANGE, label="سهم از مبلغ اعطاشده")
    for b in list(b1) + list(b2):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1, fd(f"{b.get_height():.1f}"), ha="center", fontsize=9.5)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.yaxis.set_major_formatter(FuncFormatter(pct0))
    ax.set_xlabel("مبلغ اعطاشده‌ی قرارداد (تومان)")
    ax.set_ylabel("سهم (درصد)")
    ax.legend(frameon=False)
    ax.grid(axis="x", visible=False)
    save(fig, "loan_size_histogram.png")


def ch5_maturity():
    d = pd.read_csv(D / "loan_maturity_profile.csv")
    labels = ["سررسیدگذشته", "کمتر از ۹۰ روز", "۹۱ تا ۳۶۵ روز", "۱ تا ۳ سال", "۳ تا ۵ سال", "۵ تا ۱۰ سال", "بیش از ۱۰ سال"]
    fig, ax = plt.subplots(figsize=(10, 4.4))
    hbar(ax, labels, d.balance_share_pct, BLUE, fmt=lambda v: fd(f"{v:.1f}"), xlabel="سهم از مانده‌ی قابل تحلیل (درصد)", suffix="٪")
    save(fig, "loan_maturity_profile.png")


def ch5_rate():
    d = pd.read_csv(D / "rate_by_type_balance_weighted.csv").sort_values("rate_bal_weighted", ascending=False)
    fig, ax = plt.subplots(figsize=(10, 4.4))
    hbar(ax, list(d.grp), d.rate_bal_weighted, BLUE, fmt=lambda v: fd(f"{v:.2f}"), xlabel="نرخ مؤثر قراردادی (درصد، وزن مانده‌ی ۱۲/۱۴۰۴)", suffix="٪")
    ax.axvline(10.46, color=RED, ls="--", lw=1.4)
    ax.text(10.7, 0.1, "هزینه‌ی تأمین مالی ۱۴۰۴: " + fd("10.46") + " درصد", color=RED, fontsize=10, va="bottom")
    save(fig, "effective_rate_loan_by_type.png")


def ch5_collateral(kind):
    if kind == "type":
        d = pd.read_csv(D / "collateral_coverage_by_loan_type.csv").sort_values("coverage_pct", ascending=False)
        labels, name = list(d.loan_type_group), "collateral_coverage_by_loan_type.png"
    else:
        d = pd.read_csv(D / "collateral_coverage_by_sector.csv").sort_values("coverage_pct", ascending=False)
        nm = {"اعتباراسنادی": "اعتبارات اسنادی", "صنایع تبدیلی بخش کشاورزی": "صنایع تبدیلی کشاورزی"}
        labels, name = [nm.get(v, v) for v in d.economic_sector], "collateral_coverage_by_sector.png"
    cols = [RED if v < 100 else BLUE for v in d.coverage_pct]
    fig, ax = plt.subplots(figsize=(10, 4.4))
    hbar(ax, labels, d.coverage_pct, cols, fmt=lambda v: fd(f"{v:.1f}"), xlabel="نسبت پوشش وثیقه (درصد مبلغ اعطاشده)", suffix="٪")
    ax.axvline(100, color=GREY, ls="--", lw=1.2)
    save(fig, name)


# ------------------------------------------------------------------ فصل ۶
def ch6_classification():
    r = pd.read_csv(D / "receivables_classification_trend_full.csv")
    yms = r.year_month.astype(int).tolist()
    x = range(len(yms))
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), gridspec_kw={"width_ratios": [1.1, 1]})
    axes[0].stackplot(x, r.current_balance / T, (r.overusance_balance + r.postponed_balance + r.doubtful_balance) / T,
                      colors=[LIGHT, RED], labels=["جاری", "غیرجاری"])
    axes[0].set_title("کل مانده‌ی تسهیلات نمونه", fontsize=12, color=BLUE)
    axes[0].yaxis.set_major_formatter(FuncFormatter(fmt0))
    axes[0].set_ylabel("هزار میلیارد تومان")
    axes[0].legend(frameon=False, loc="upper left")
    axes[1].stackplot(x, r.overusance_balance / T, r.postponed_balance / T, r.doubtful_balance / T,
                      colors=["#E3B341", ORANGE, RED], labels=["سررسیدگذشته", "معوق", "مشکوک‌الوصول"])
    axes[1].set_title("طبقات مطالبات غیرجاری", fontsize=12, color=BLUE)
    axes[1].yaxis.set_major_formatter(FuncFormatter(fmt1))
    axes[1].legend(frameon=False, loc="upper left")
    for ax in axes:
        time_axis(ax, yms, 12)
    save(fig, "ch6_classification_trend.png")


def ch6_lc():
    l = pd.read_csv(D / "letters_of_credit_npl_trend.csv")
    yms = l.year_month.astype(int).tolist()
    fig, ax = plt.subplots(figsize=(11, 4.4))
    ax.plot(range(len(yms)), l.loc_npl_ratio_pct, color=RED, lw=2.2, label="اعتبارات اسنادی")
    ax.plot(range(len(yms)), l.other_npl_ratio_pct, color=BLUE, lw=2.2, label="سایر پرتفوی")
    time_axis(ax, yms)
    ax.yaxis.set_major_formatter(FuncFormatter(pct0))
    ax.set_ylabel("نسبت مطالبات غیرجاری")
    ax.legend(frameon=False, loc="upper left")
    save(fig, "ch6_lc_npl_trend.png")


def bars_with_ratio(name, labels, bal, ratio, xlabel, balance_label="مانده (هزار میلیارد تومان)"):
    x = np.arange(len(labels))
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4))
    b = axes[0].bar(x, bal, color=LIGHT, width=0.62)
    for bi, v in zip(b, bal):
        axes[0].text(bi.get_x() + bi.get_width() / 2, v + max(bal) * 0.015, fmt1(v), ha="center", fontsize=9.5)
    axes[0].set_ylabel(balance_label)
    b2 = axes[1].bar(x, ratio, color=ORANGE, width=0.62)
    for bi, v in zip(b2, ratio):
        axes[1].text(bi.get_x() + bi.get_width() / 2, v + max(ratio) * 0.015, fd(f"{v:.1f}") + "٪", ha="center", fontsize=9.5)
    axes[1].set_ylabel("نسبت مطالبات غیرجاری (درصد)")
    for ax in axes:
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=9.5)
        ax.set_xlabel(xlabel)
        ax.grid(axis="x", visible=False)
    save(fig, name)


def ch6_size():
    d = pd.read_csv(D / "npl_by_loan_size.csv")
    labels = ["کمتر از ۵۰\nمیلیون", "۵۰ تا ۲۰۰\nمیلیون", "۲۰۰ میلیون\nتا ۱ میلیارد", "۱ تا ۵\nمیلیارد", "بیش از ۵\nمیلیارد"]
    bars_with_ratio("npl_by_loan_size.png", labels, d.total_balance / T, d.npl_ratio_pct, "مبلغ اعطاشده‌ی وام (تومان)")


def ch6_branch():
    d = pd.read_csv(D / "npl_by_branch_size.csv")
    labels = ["کوچک‌ترین\nچارک", "چارک دوم", "چارک سوم", "بزرگ‌ترین\nچارک"]
    bars_with_ratio("npl_by_branch_size.png", labels, d.total_balance / T, d.npl_ratio_pct, "چارک اندازه‌ی شعبه (بر حسب مانده‌ی تسهیلات)")


def ch6_vintage():
    d = pd.read_csv(D / "loan_vintage_analysis.csv")
    labels = [fd(v) for v in d.grant_year]
    bars_with_ratio("loan_vintage_analysis.png", labels, d.total_balance / T, d.npl_ratio_pct, "سال اعطای تسهیلات")


def ch6_guarantor():
    d = pd.read_csv(D / "guarantor_complexity_npl.csv")
    d = d[d.guarantor_bucket.isin(["۱ (تک‌ضامنی)", "۲-۳", "۴-۶"])].reset_index(drop=True)
    ex = [5.45, 5.11, 8.71]  # نسبت بدون اعتبارات اسنادی؛ خروجی 23_v4_review_checks.py
    labels = ["یک طرف", "دو تا سه طرف", "چهار تا شش طرف"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
    x = np.arange(3)
    b = axes[0].bar(x, d.loan_count / 1e3, color=LIGHT, width=0.6)
    for bi, v in zip(b, d.loan_count / 1e3):
        axes[0].text(bi.get_x() + bi.get_width() / 2, v + 12, fmt0(v), ha="center", fontsize=9.5)
    axes[0].set_ylabel("تعداد قرارداد (هزار)")
    b1 = axes[1].bar(x - 0.2, d.npl_ratio_pct, 0.38, color=ORANGE, label="کل پرتفوی")
    b2 = axes[1].bar(x + 0.2, ex, 0.38, color=BLUE, label="بدون اعتبارات اسنادی")
    for bi in list(b1) + list(b2):
        axes[1].text(bi.get_x() + bi.get_width() / 2, bi.get_height() + 0.2, fd(f"{bi.get_height():.2f}"), ha="center", fontsize=9.5)
    axes[1].set_ylabel("نسبت مطالبات غیرجاری (درصد)")
    axes[1].legend(frameon=False, loc="upper right")
    for ax in axes:
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_xlabel("تعداد طرف‌های قرارداد")
        ax.grid(axis="x", visible=False)
    save(fig, "guarantor_complexity_npl.png")


def ch6_transition():
    d = pd.read_csv(D / "transition_matrix_raw.csv")
    order = ["jari", "sarresid", "moaavagh", "mashkook", "X"]
    labels = ["جاری", "سررسیدگذشته", "معوق", "مشکوک‌الوصول", "بدون مانده"]
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.2))
    for ax, ym, title in zip(axes, [140311, 140411], ["۱۱/۱۴۰۳ تا ۱۲/۱۴۰۳", "۱۱/۱۴۰۴ تا ۱۲/۱۴۰۴"]):
        p = d[d.from_year_month == ym].pivot_table(index="from_status", columns="to_status", values="cnt", aggfunc="sum", fill_value=0)
        p = p.reindex(index=order, columns=order, fill_value=0)
        pct = p.div(p.sum(axis=1), axis=0) * 100
        ax.imshow(pct.values, cmap="YlOrRd", vmin=0, vmax=100)
        ax.set_xticks(range(5))
        ax.set_yticks(range(5))
        ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=9.5)
        ax.set_yticklabels(labels, fontsize=9.5)
        ax.set_title(fd(title), fontsize=12, color=BLUE)
        ax.set_xlabel("طبقه‌ی ماه بعد")
        ax.set_ylabel("طبقه‌ی ماه پایه")
        ax.grid(False)
        for i in range(5):
            for j in range(5):
                v = pct.values[i, j]
                ax.text(j, i, fd(f"{v:.0f}"), ha="center", va="center", fontsize=10, color="white" if v > 55 else "black")
    save(fig, "risk_transition_matrix.png")


def ch6_dpd():
    d = pd.read_csv(D / "dpd_distribution_overall.csv")
    labels = ["قسط آتی (سررسید نشده)", "پرداخت در سررسید یا زودتر", "یک تا هفت روز دیرکرد", "هشت تا سی روز دیرکرد",
              "سی‌ویک تا نود روز دیرکرد", "بیش از نود روز دیرکرد"]
    fig, ax = plt.subplots(figsize=(10, 4.4))
    hbar(ax, labels, d.share_pct, BLUE, fmt=lambda v: fd(f"{v:.2f}"), xlabel="سهم از کل اقساط (درصد)", suffix="٪")
    save(fig, "dpd_distribution_overall.png")


def ch6_single_name():
    d = pd.read_csv(D / "single_name_concentration_top20.csv").sort_values("rank")
    labels = [f"مشتری {fd(int(r))}" for r in d["rank"]]
    fig, ax = plt.subplots(figsize=(9.5, 6.4))
    y = np.arange(len(labels))[::-1]
    ax.barh(y, d.total_exposure / T, color=BLUE, height=0.65)
    for yi, v in zip(y, d.total_exposure / T):
        ax.text(v + 0.05, yi, fmt1(v), va="center", fontsize=9.5)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlabel("مانده‌ی تسهیلات (هزار میلیارد تومان)")
    ax.grid(axis="y", visible=False)
    save(fig, "single_name_concentration_top20.png")


if __name__ == "__main__":
    for f in (ch4_deposit_trend, ch4_yoy, ch4_composition, ch4_ladder, ch4_lorenz, ch5_ldr, ch5_loan_type, ch5_sector,
              ch5_size, ch5_maturity, ch5_rate, lambda: ch5_collateral("type"), lambda: ch5_collateral("sector"),
              ch6_classification, ch6_lc, ch6_size, ch6_branch, ch6_vintage, ch6_guarantor, ch6_transition, ch6_dpd,
              ch6_single_name):
        f()
