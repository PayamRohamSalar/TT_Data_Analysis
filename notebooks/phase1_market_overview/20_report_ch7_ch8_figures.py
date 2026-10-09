"""نمودارها و جدول‌های تحلیلی فصل ۷ (جغرافیا) و فصل ۸ (سودآوری) گزارش فاز ۱.

ورودی: فقط فایل‌های خروجی موجود در data/processed/phase1_market_overview (بدون اتصال پایگاه‌داده).
خروجی: نمودارها در reports/figures/phase1_market_overview و فایل ch7_province_indicators.csv /
ch8_tables.json برای درج جدول‌ها در گزارش.
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter

from tt_bank.common.persian_plot import FONTS_DIR, setup_persian_font, to_persian_digits

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "reports" / "figures" / "phase1_market_overview"
PROC = ROOT / "data" / "processed" / "phase1_market_overview"
setup_persian_font()
font_manager.fontManager.addfont(str(FONTS_DIR / "Vazirmatn-Bold.ttf"))

BLUE, ORANGE, GREEN, GREY, LIGHT, MID = "#1F4E79", "#C55A11", "#548235", "#7F7F7F", "#D9E2EF", "#9DC3E6"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#888888",
                     "font.size": 11, "savefig.dpi": 200})
NONGEO = ["ستاد", "ستاد-امورمالی", "شعب مستقل"]
pd_ = to_persian_digits
num = lambda x: pd_(f"{x:,.0f}")
pct = lambda v, d=1: pd_(f"{v:.{d}f}") + "٪"
LAST, FIRST = 140412, 140001


def save(fig, name):
    fig.savefig(FIG / name, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", name)


def load():
    p = pd.read_csv(PROC / "bank_official_monthly_by_province.csv")
    b = pd.read_csv(PROC / "bank_official_monthly_by_branch.csv")
    return p, b


def province_table(p, b):
    l = p[p.year_month == LAST].set_index("province")
    f = p[p.year_month == FIRST].set_index("province")
    tot_r, tot_l, tot_n = l.rial_resources.sum(), l.loans.sum(), l.npl.sum()
    t = pd.DataFrame(index=l.index)
    t["resources"] = l.rial_resources / 1e13
    t["loans"] = l.loans / 1e13
    t["npl"] = l.npl / 1e13
    t["res_share"] = l.rial_resources / tot_r * 100
    t["loan_share"] = l.loans / tot_l * 100
    t["ldr"] = l.loans / l.rial_resources * 100
    t["net"] = (l.rial_resources - l.loans) / 1e13
    t["npl_ratio"] = l.npl / l.loans * 100
    t["res_mult"] = l.rial_resources / f.rial_resources
    t["loan_mult"] = l.loans / f.loans
    bl = b[(b.year_month == LAST) & (~b.is_admin_unit)]
    t["branches"] = bl.groupby("province").size()
    t["res_per_branch"] = t.resources / t.branches
    return t.drop(index=[x for x in NONGEO if x in t.index]), t, (tot_r, tot_l, tot_n)


def fig_province_shares(t):
    d = t.sort_values("res_share", ascending=False).head(15)
    y = np.arange(len(d))[::-1]
    h = 0.38
    fig, ax = plt.subplots(figsize=(9.5, 6.2))
    ax.barh(y + h / 2, d.res_share, h, color=BLUE, label="سهم از منابع ریالی بانک")
    ax.barh(y - h / 2, d.loan_share, h, color=ORANGE, label="سهم از تسهیلات بانک")
    for yy, a, c in zip(y, d.res_share, d.loan_share):
        ax.text(a + 0.3, yy + h / 2, pct(a), va="center", fontsize=9.5)
        ax.text(c + 0.3, yy - h / 2, pct(c), va="center", fontsize=9.5)
    ax.set_yticks(y)
    ax.set_yticklabels(d.index, fontsize=10.5)
    ax.set_xlim(0, 27)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: pd_(f"{v:.0f}") + "٪"))
    ax.set_xlabel("سهم از کل بانک (۱۲/۱۴۰۴)")
    ax.legend(frameon=False, loc="lower right", fontsize=10.5)
    save(fig, "ch7_province_shares.png")


def fig_province_ldr(t):
    d = t.sort_values("ldr", ascending=True)
    y = np.arange(len(d))
    fig, ax = plt.subplots(figsize=(9, 9))
    ax.barh(y, d.ldr, color=[BLUE if v <= 100 else ORANGE for v in d.ldr], height=0.7)
    ax.axvline(100, color="#444444", ls="--", lw=1.2)
    ax.axvline(111.3, color=GREEN, ls=":", lw=1.6)
    ax.text(111.3, len(d) + 0.3, "میانگین بانک: " + pct(111.3), color=GREEN, ha="left", fontsize=10)
    for yy, v in zip(y, d.ldr):
        ax.text(v + 2, yy, pd_(f"{v:.0f}") + "٪", va="center", fontsize=9)
    ax.set_yticks(y)
    ax.set_yticklabels(d.index, fontsize=10)
    ax.set_xlim(0, 235)
    ax.set_ylim(-0.7, len(d) + 0.9)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: pd_(f"{v:.0f}") + "٪"))
    ax.set_xlabel("نسبت تسهیلات به منابع ریالی (۱۲/۱۴۰۴)")
    save(fig, "ch7_province_ldr.png")


def fig_province_npl(t, tall, totals):
    tot_r, tot_l, tot_n = totals
    d = t.sort_values("npl_ratio", ascending=True)
    hi = d[d.npl_ratio > 15].index
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 8.2), gridspec_kw={"width_ratios": [1.7, 1]})
    y = np.arange(len(d))
    a1.barh(y, d.npl_ratio, color=[ORANGE if i in hi else BLUE for i in d.index], height=0.7)
    a1.axvline(8.0, color=GREEN, ls=":", lw=1.6)
    a1.text(8.3, len(d) - 0.2, "میانگین بانک: " + pct(8.0), color=GREEN, fontsize=10)
    for yy, v in zip(y, d.npl_ratio):
        a1.text(v + 0.4, yy, pd_(f"{v:.1f}") + "٪", va="center", fontsize=8.5)
    a1.set_yticks(y)
    a1.set_yticklabels(d.index, fontsize=9.5)
    a1.set_xlim(0, 42)
    a1.xaxis.set_major_formatter(FuncFormatter(lambda v, _: pd_(f"{v:.0f}") + "٪"))
    a1.set_xlabel("نسبت مطالبات غیرجاری (۱۲/۱۴۰۴)")
    g_loan = tall.loc[hi].loans.sum() / (tot_l / 1e13) * 100
    g_npl = tall.loc[hi].npl.sum() / (tot_n / 1e13) * 100
    a2.bar([0 - 0.19, 1 - 0.19], [g_loan, 100 - g_loan - 0], 0.0)  # placeholder to keep axes consistent
    a2.cla()
    a2.bar([-0.2], [g_loan], 0.38, color=MID, label="سهم از تسهیلات")
    a2.bar([0.2], [g_npl], 0.38, color=ORANGE, label="سهم از مطالبات غیرجاری")
    a2.text(-0.2, g_loan + 1, pct(g_loan), ha="center")
    a2.text(0.2, g_npl + 1, pct(g_npl), ha="center")
    a2.set_xticks([0])
    a2.set_xticklabels(["چهار استان با نسبت\nغیرجاری بالای ۱۸٪"], fontsize=10.5)
    a2.set_ylim(0, 50)
    a2.yaxis.set_major_formatter(FuncFormatter(lambda v, _: pd_(f"{v:.0f}") + "٪"))
    a2.legend(frameon=False, loc="upper left", fontsize=10)
    save(fig, "ch7_province_npl.png")
    return g_loan, g_npl, list(hi)


def fig_province_growth(t):
    d = t.sort_values("loan_mult")
    y = np.arange(len(d))
    fig, ax = plt.subplots(figsize=(9.5, 9))
    for yy, a, c in zip(y, d.res_mult, d.loan_mult):
        ax.plot([a, c], [yy, yy], color="#BBBBBB", lw=1.2, zorder=1)
    ax.scatter(d.res_mult, y, color=BLUE, s=38, label="منابع ریالی", zorder=2)
    ax.scatter(d.loan_mult, y, color=ORANGE, s=38, label="تسهیلات", zorder=2)
    ax.set_yticks(y)
    ax.set_yticklabels(d.index, fontsize=10)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: pd_(f"{v:.0f}")))
    ax.set_xlabel("چند برابر شدن از ۰۱/۱۴۰۰ تا ۱۲/۱۴۰۴ (برابر)")
    ax.grid(axis="x", color="#E8E8E8")
    ax.legend(frameon=False, loc="lower right", fontsize=10.5)
    save(fig, "ch7_province_growth.png")


def fig_funding_mix_province(p):
    l = p[p.year_month == 140410].set_index("province")
    l = l.drop(index=[x for x in NONGEO if x in l.index])
    d = pd.DataFrame({"free": (l.gharz_current + l.gharz_saving) / l.rial_resources * 100,
                      "short": l.short_term / l.rial_resources * 100, "long": l.long_term / l.rial_resources * 100})
    d = d.sort_values("free")
    y = np.arange(len(d))
    fig, ax = plt.subplots(figsize=(9.5, 9))
    ax.barh(y, d.free, color=GREEN, height=0.72, label="قرض‌الحسنه (جاری و پس‌انداز)")
    ax.barh(y, d.short, left=d.free, color=MID, height=0.72, label="کوتاه‌مدت")
    ax.barh(y, d.long, left=d.free + d.short, color=BLUE, height=0.72, label="بلندمدت")
    ax.set_yticks(y)
    ax.set_yticklabels(d.index, fontsize=10)
    ax.set_xlim(0, 100)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: pd_(f"{v:.0f}") + "٪"))
    ax.set_xlabel("ترکیب منابع ریالی هر استان (۱۰/۱۴۰۴)")
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.07), ncol=3, fontsize=10)
    save(fig, "ch7_funding_mix_province.png")
    return d


def lorenz_stats(x):
    x = np.sort(np.asarray(x, float))
    x = x[x > 0]
    c = np.cumsum(x) / x.sum()
    n = len(x)
    gini = 1 - 2 * np.sum((np.r_[0, c][:-1] + np.r_[0, c][1:]) / 2) / n
    top10 = x[-int(np.ceil(n * 0.1)):].sum() / x.sum()
    top20 = x[-int(np.ceil(n * 0.2)):].sum() / x.sum()
    return c, gini, top10, top20, n


def fig_branch_concentration(b):
    bl = b[(b.year_month == LAST) & (~b.is_admin_unit) & (~b.province.isin(NONGEO))]
    fig, ax = plt.subplots(figsize=(7.2, 6.2))
    stats = {}
    for col, c, lab in (("rial_resources", BLUE, "منابع ریالی"), ("loans", ORANGE, "تسهیلات")):
        cum, g, t10, t20, n = lorenz_stats(bl[col].values)
        xs = np.r_[0, np.arange(1, n + 1) / n]
        ax.plot(xs, np.r_[0, cum], color=c, lw=2.2, label=f"{lab} (ضریب جینی {pd_(f'{g:.2f}')})")
        stats[col] = dict(gini=g, top10=t10, top20=t20, n=n)
    ax.plot([0, 1], [0, 1], color="#999999", ls="--", lw=1)
    ax.set_xlabel("سهم تجمعی شعب (از کوچک به بزرگ)")
    ax.set_ylabel("سهم تجمعی از کل")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: pd_(f"{v*100:.0f}") + "٪"))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: pd_(f"{v*100:.0f}") + "٪"))
    ax.legend(frameon=False, loc="upper left", fontsize=10.5)
    ax.grid(color="#EEEEEE")
    save(fig, "ch7_branch_concentration.png")
    return stats


def fig_sample_vs_official():
    d = pd.read_csv(PROC / "province_sample_vs_official_140412.csv").set_index("province")
    d = d.drop(index=[x for x in NONGEO if x in d.index])
    so = d.official_loans / d.official_loans.sum() * 100
    ss = d.sample_loans / d.sample_loans.sum() * 100
    cov = (d.sample_loans / d.official_loans * 100).sort_values()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 6.6), gridspec_kw={"width_ratios": [1, 1.1]})
    a1.scatter(so, ss, color=BLUE, s=34, zorder=3)
    mx = max(so.max(), ss.max()) * 1.05
    a1.plot([0, mx], [0, mx], color=GREY, ls="--", lw=1)
    offs = {"تهران": (6, -12), "اصفهان": (8, -4), "خوزستان": (8, -12), "مازندران": (8, 4), "فارس": (-42, 6)}
    for nm, off_ in offs.items():
        a1.annotate(nm, (so[nm], ss[nm]), textcoords="offset points", xytext=off_, fontsize=9.5)
    r = np.corrcoef(np.log(d.sample_loans), np.log(d.official_loans))[0, 1]
    a1.text(0.04, 0.93, "ضریب همبستگی (لگاریتمی): " + pd_(f"{r:.2f}"), transform=a1.transAxes, color=BLUE, fontsize=10.5)
    a1.set_xlabel("سهم استان از تسهیلات بانک — آمار رسمی")
    a1.set_ylabel("سهم استان از تسهیلات — نمونه")
    for ax_ in (a1,):
        ax_.xaxis.set_major_formatter(FuncFormatter(lambda v, _: pd_(f"{v:.0f}") + "٪"))
        ax_.yaxis.set_major_formatter(FuncFormatter(lambda v, _: pd_(f"{v:.0f}") + "٪"))
    y = np.arange(len(cov))
    a2.barh(y, cov.values, color=MID, height=0.7)
    a2.axvline(cov.mean(), color=ORANGE, ls="--", lw=1.3)
    a2.text(cov.mean() + 1, len(cov) - 0.5, "میانگین: " + pct(cov.mean(), 0), color=ORANGE, fontsize=10)
    a2.set_yticks(y)
    a2.set_yticklabels(cov.index, fontsize=8.5)
    a2.set_xlim(0, 100)
    a2.xaxis.set_major_formatter(FuncFormatter(lambda v, _: pd_(f"{v:.0f}") + "٪"))
    a2.set_xlabel("پوشش تسهیلات هر استان در نمونه (بخش دارای نگاشت شعبه)")
    save(fig, "ch7_sample_vs_official_province.png")
    dep = d[d.sample_deposit_inferred > 0]
    rd = np.corrcoef(np.log(dep.sample_deposit_inferred), np.log(dep.official_resources))[0, 1]
    return dict(r_loans=r, r_deposits=rd, cov_mean=cov.mean(), cov_min=cov.min(), cov_max=cov.max(),
                cov_min_p=cov.index[0], cov_max_p=cov.index[-1])


def fig_customers_province(t):
    c = pd.read_csv(PROC / "province_customers_home_branch.csv").set_index("province")
    c = c.drop(index=[x for x in NONGEO if x in c.index])
    cs = c.customers / c.customers.sum() * 100
    rs = t.res_share / t.res_share.sum() * 100
    d = pd.DataFrame({"cust": cs, "res": rs}).dropna().sort_values("cust", ascending=False).head(12)
    y = np.arange(len(d))[::-1]
    h = 0.38
    fig, ax = plt.subplots(figsize=(9, 5.8))
    ax.barh(y + h / 2, d.cust, h, color=BLUE, label="سهم از مشتریان نمونه")
    ax.barh(y - h / 2, d.res, h, color=MID, label="سهم از منابع ریالی بانک (آمار رسمی)")
    for yy, a, b_ in zip(y, d.cust, d.res):
        ax.text(a + 0.3, yy + h / 2, pct(a), va="center", fontsize=9.5)
        ax.text(b_ + 0.3, yy - h / 2, pct(b_), va="center", fontsize=9.5)
    ax.set_yticks(y)
    ax.set_yticklabels(d.index, fontsize=10.5)
    ax.set_xlim(0, max(d.cust.max(), d.res.max()) * 1.2)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: pd_(f"{v:.0f}") + "٪"))
    ax.set_xlabel("سهم از جمع استان‌ها")
    ax.legend(frameon=False, loc="lower right", fontsize=10)
    save(fig, "ch7_customers_province.png")
    return d, int(c.customers.sum())


# ------------------------------ chapter 8 ------------------------------
def year_tables():
    pl = pd.read_csv(PROC / "profit_and_loss_estimate.csv")
    pl["y"] = pl.year_month // 100
    rc = pd.read_csv(PROC / "receivables_classification_trend_full.csv")
    rc["y"] = rc.year_month // 100
    off = pd.read_csv(PROC / "bank_official_monthly.csv")
    off["y"] = off.year_month // 100
    ri = pd.read_csv(PROC / "bank_reference_interest_monthly.csv")
    led = pd.read_csv(PROC / "ledger_coverage_by_year.csv").set_index("year") if (PROC / "ledger_coverage_by_year.csv").exists() else None
    rows = []
    for y in range(1400, 1405):
        inc_i = pl[pl.y == y].loan_interest_income.sum() / 1e13
        inc_p = pl[pl.y == y].loan_penalty_income.sum() / 1e13
        fee = pl[pl.y == y].fee_income.sum() / 1e13
        avg_s = rc[rc.y == y].total_balance.mean() / 1e13
        avg_res = off[(off.y == y) & (off.rial_resources_pure == True)].rial_resources.mean() / 1e13
        avg_loan = off[off.y == y].loans.mean() / 1e13
        cost = ri[ri.ym // 100 == y].amount.sum() / 1e13
        rows.append(dict(year=y, interest_income=inc_i, penalty_income=inc_p, fee_income=fee, avg_sample_loans=avg_s,
                         realized_yield=(inc_i + inc_p) / avg_s * 100, avg_official_loans=avg_loan,
                         avg_official_resources=avg_res, official_interest_cost=cost, cost_rate=cost / avg_res * 100,
                         avg_ledger_loans=(led.loc[y, "ledger"] if led is not None else np.nan),
                         yield_covered=((inc_i + inc_p) / led.loc[y, "ledger"] * 100 if led is not None else np.nan)))
    return pd.DataFrame(rows)


def fig_funding_cost(yt):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.5, 4.8))
    x = np.arange(len(yt))
    a1.bar(x - 0.2, yt.avg_official_resources, 0.38, color=MID, label="میانگین منابع ریالی")
    a1.bar(x + 0.2, yt.official_interest_cost, 0.38, color=ORANGE, label="سود پرداختی (آمار مرجع بانک)")
    for i, (a, c) in enumerate(zip(yt.avg_official_resources, yt.official_interest_cost)):
        a1.text(i - 0.2, a + 1.5, pd_(f"{a:.1f}"), ha="center", fontsize=9.5)
        a1.text(i + 0.2, c + 1.5, pd_(f"{c:.1f}"), ha="center", fontsize=9.5)
    a1.set_xticks(x)
    a1.set_xticklabels([pd_(str(v)) for v in yt.year])
    a1.set_ylabel("هزار میلیارد تومان")
    a1.yaxis.set_major_formatter(FuncFormatter(lambda v, _: pd_(f"{v:.0f}")))
    a1.legend(frameon=False, loc="upper left", fontsize=10)
    a1.set_title("منابع و سود پرداختی سالانه", fontsize=12, color=BLUE)
    a2.plot(x, yt.cost_rate, color=ORANGE, lw=2.4, marker="o")
    for i, v in enumerate(yt.cost_rate):
        a2.text(i, v + 0.25, pct(v), ha="center", fontsize=10.5)
    a2.set_xticks(x)
    a2.set_xticklabels([pd_(str(v)) for v in yt.year])
    a2.set_ylim(6, 12.5)
    a2.yaxis.set_major_formatter(FuncFormatter(lambda v, _: pd_(f"{v:.0f}") + "٪"))
    a2.set_title("نرخ هزینه‌ی تأمین مالی (سود پرداختی ÷ میانگین منابع)", fontsize=12, color=ORANGE)
    a2.grid(axis="y", color="#EEEEEE")
    save(fig, "ch8_funding_cost.png")


def fig_funding_mix_trend(p):
    g = p.groupby("year_month").apply(lambda d: pd.Series({
        "free": (d.gharz_current.sum() + d.gharz_saving.sum()) / d.rial_resources.sum() * 100,
        "short": d.short_term.sum() / d.rial_resources.sum() * 100,
        "long": d.long_term.sum() / d.rial_resources.sum() * 100,
        "rel": bool(d.deposit_breakdown_reliable.all())}), include_groups=False).reset_index()
    g = g[g.rel == True].reset_index(drop=True)
    g = g[g.year_month <= 140410]
    idx = np.arange(len(g))
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.stackplot(idx, g.free, g.short, g.long, colors=[GREEN, MID, BLUE], labels=["قرض‌الحسنه (جاری و پس‌انداز)", "کوتاه‌مدت", "بلندمدت"])
    ticks = [i for i in range(len(g)) if g.year_month[i] % 100 == 1] + [len(g) - 1]
    ax.set_xticks(ticks)
    ax.set_xticklabels([pd_(f"{str(g.year_month[i])[4:]}/{str(g.year_month[i])[:4]}") for i in ticks], fontsize=9.5)
    ax.set_ylim(0, 100)
    ax.set_xlim(0, len(g) - 1)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: pd_(f"{v:.0f}") + "٪"))
    ax.set_ylabel("سهم از منابع ریالی")
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.12), ncol=3, fontsize=10)
    save(fig, "ch8_funding_mix_trend.png")
    return g


def fig_loan_yield_by_type(cost_rate):
    d = pd.read_csv(PROC / "rate_by_type_balance_weighted.csv").sort_values("rate_bal_weighted")
    d["share"] = d.balance / d.balance.sum() * 100
    y = np.arange(len(d))
    fig, ax = plt.subplots(figsize=(9.5, 5))
    ax.barh(y, d.rate_bal_weighted, color=[BLUE if r > cost_rate else MID for r in d.rate_bal_weighted], height=0.62)
    ax.axvline(cost_rate, color=ORANGE, ls="--", lw=1.6)
    ax.text(cost_rate + 0.3, len(d) - 0.35, "نرخ هزینه‌ی تأمین مالی ۱۴۰۴: " + pct(cost_rate, 2), color=ORANGE, fontsize=10)
    for yy, r, sh in zip(y, d.rate_bal_weighted, d.share):
        ax.text(r + 0.3, yy, pd_(f"{r:.1f}") + "٪  (سهم از مانده " + pd_(f"{sh:.1f}") + "٪)", va="center", fontsize=9.5)
    ax.set_yticks(y)
    ax.set_yticklabels(d.grp, fontsize=10.5)
    ax.set_xlim(0, 36)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: pd_(f"{v:.0f}") + "٪"))
    ax.set_xlabel("نرخ سود قراردادی (وزن‌دهی‌شده بر مانده‌ی ۱۲/۱۴۰۴)")
    save(fig, "ch8_loan_yield_by_type.png")
    return d


def fig_yield_vs_cost(yt, contractual):
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(yt))
    ax.plot(x, yt.cost_rate, color=ORANGE, lw=2.4, marker="o", label="نرخ هزینه‌ی تأمین مالی (آمار رسمی بانک)")
    ax.plot(x, yt.yield_covered, color=GREEN, lw=2.4, marker="D", label="بازده درآمد دریافتی بر قراردادهای دارای دفتر اقساط")
    ax.plot(x, yt.realized_yield, color=BLUE, lw=2.0, marker="s", ls="--", label="بازده درآمد دریافتی بر کل مانده‌ی نمونه")
    ax.scatter([x[-1]], [contractual], color="#7F7F7F", s=110, zorder=5, marker="*", label="نرخ قراردادی (وزن مانده، ۱۲/۱۴۰۴)")
    for i in range(len(yt)):
        ax.text(i, yt.cost_rate[i] - 0.9, pct(yt.cost_rate[i]), ha="center", color=ORANGE, fontsize=9.5)
        ax.text(i, yt.yield_covered[i] + 0.45, pct(yt.yield_covered[i]), ha="center", color=GREEN, fontsize=9.5)
        ax.text(i, yt.realized_yield[i] - 0.95, pct(yt.realized_yield[i]), ha="center", color=BLUE, fontsize=9.5)
    ax.text(x[-1] - 0.05, contractual + 0.5, pct(contractual, 2), ha="right", color="#555555", fontsize=10.5)
    ax.set_xticks(x)
    ax.set_xticklabels([pd_(str(v)) for v in yt.year])
    ax.set_ylim(4, 21)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: pd_(f"{v:.0f}") + "٪"))
    ax.grid(axis="y", color="#EEEEEE")
    ax.legend(frameon=False, loc="upper left", fontsize=9.5)
    save(fig, "ch8_yield_vs_cost.png")


def main():
    p, b = load()
    t, tall, totals = province_table(p, b)
    t.round(4).to_csv(PROC / "ch7_province_indicators.csv", encoding="utf-8-sig")
    out = {}
    fig_province_shares(t)
    fig_province_ldr(t)
    gl, gn, hi = fig_province_npl(t, tall, totals)
    out["npl_group"] = dict(loan_share=gl, npl_share=gn, provinces=hi)
    fig_province_growth(t)
    mix = fig_funding_mix_province(p)
    out["mix_free_max"] = [mix.free.idxmax(), float(mix.free.max())]
    out["mix_free_min"] = [mix.free.idxmin(), float(mix.free.min())]
    out["branch"] = fig_branch_concentration(b)
    out["sample_vs_official"] = fig_sample_vs_official()
    d, ncust = fig_customers_province(t)
    out["customers_total"] = ncust
    out["customers_top"] = d.round(2).reset_index().to_dict("records")
    yt = year_tables()
    yt.round(4).to_csv(PROC / "ch8_yearly.csv", index=False)
    fig_funding_cost(yt)
    mixt = fig_funding_mix_trend(p)
    out["mix_trend_first"] = mixt.iloc[0].to_dict()
    out["mix_trend_last"] = mixt.iloc[-1].to_dict()
    cost_rate = float(yt.cost_rate.iloc[-1])
    lt = fig_loan_yield_by_type(cost_rate)
    rb = pd.read_csv(PROC / "rate_by_type_balance_weighted.csv")
    contractual = float((rb.balance * rb.rate_bal_weighted).sum() / rb.balance.sum())
    fig_yield_vs_cost(yt, contractual)
    out["contractual"] = contractual
    out["loan_types"] = lt.round(3).to_dict("records")
    json.dump(out, open(PROC / "ch7_ch8_stats.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    print(yt.round(2).to_string())
    print(json.dumps(out, ensure_ascii=False, indent=1, default=float)[:3500])


if __name__ == "__main__":
    main()
