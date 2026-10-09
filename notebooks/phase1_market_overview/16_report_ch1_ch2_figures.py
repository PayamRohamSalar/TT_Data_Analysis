"""نمودارهای تحلیلی فصل‌های ۱ و ۲ گزارش فاز ۱ (طراحی نمونه‌گیری، زنجیره‌ی پردازش، پوشش نمونه).\n\nورودی: فقط فایل‌های خروجی موجود (بدون نیاز به اتصال پایگاه‌داده) و ارقام مستند توزیع کل بانک\n(docs/Sampling Method/RFM.xlsx و گزارش نمونه‌گیری).\nقالب تاریخ در تمام نمودارها: ماه/سال (مثلاً ۰۱/۱۴۰۰).\n"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch
from matplotlib.ticker import FuncFormatter

from matplotlib import font_manager

from tt_bank.common.persian_plot import FONTS_DIR, setup_persian_font, to_persian_digits

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIG_DIR = PROJECT_ROOT / "reports" / "figures" / "phase1_market_overview"
PROC_DIR = PROJECT_ROOT / "data" / "processed" / "phase1_market_overview"
FIG_DIR.mkdir(parents=True, exist_ok=True)
setup_persian_font()
font_manager.fontManager.addfont(str(FONTS_DIR / "Vazirmatn-Bold.ttf"))

BLUE, ORANGE, GREEN, GREY, LIGHT = "#1F4E79", "#C55A11", "#548235", "#7F7F7F", "#D9E2EF"
plt.rcParams.update({
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": "#888888", "axes.labelcolor": "#333333",
    "xtick.color": "#333333", "ytick.color": "#333333",
    "font.size": 11, "figure.dpi": 100, "savefig.dpi": 200,
})


def pd_(x) -> str:
    return to_persian_digits(x)


def num(x) -> str:
    return pd_(f"{x:,.0f}")


def ym_label(ym: int) -> str:
    s = str(int(ym))
    return pd_(f"{s[4:6]}/{s[:4]}")


def save(fig, name: str) -> None:
    fig.savefig(FIG_DIR / name, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", name)


def fig_sampling_funnel() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
    panels = [
        ("سپرده‌گذاران", [
            ("کل مشتریان دارای سپرده", 7_404_240, LIGHT),
            ("مشتریان فعال\n(پس از پالایش چهارمعیاره)", 1_683_775, "#8FAADC"),
            ("نمونه‌ی برنامه‌ریزی‌شده", 326_682, BLUE)]),
        ("تسهیلات‌گیرندگان", [
            ("کل مشتریان دارای\nمانده‌ی تسهیلات (۱۴۰۴)", 1_583_168, LIGHT),
            ("نمونه‌ی برنامه‌ریزی‌شده", 284_048, BLUE)]),
    ]
    for ax, (title, rows) in zip(axes, panels):
        labels = [r[0] for r in rows][::-1]
        vals = [r[1] for r in rows][::-1]
        cols = [r[2] for r in rows][::-1]
        ypos = np.arange(len(rows))
        ax.barh(ypos, vals, color=cols, height=0.55)
        top = rows[0][1]
        for y, v in zip(ypos, vals):
            share = v / top * 100
            txt = num(v) + ("\n" + pd_(f"{share:.1f}") + "٪ از کل" if v != top else "")
            ax.text(v + top * 0.015, y, txt, va="center", ha="left", fontsize=10.5, linespacing=1.4)
        ax.set_yticks(ypos)
        ax.set_yticklabels(labels, fontsize=10.5)
        ax.set_xlim(0, top * 1.55)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: pd_(f"{v/1e6:.1f}")))
        ax.set_xlabel("تعداد مشتری (میلیون نفر)")
        ax.set_title(title, fontsize=13, color=BLUE, pad=10)
    fig.text(0.5, -0.03, "منبع: گزارش راهبرد نمونه‌گیری و فایل توزیع مشتریان بانک (مقطع آذر ۱۴۰۴)؛ مشتریان حقوقی به‌صورت سرشماری کامل در نمونه آمده‌اند.",
             ha="center", fontsize=9.5, color=GREY)
    save(fig, "ch1_sampling_funnel.png")


def fig_pipeline() -> None:
    fig, ax = plt.subplots(figsize=(13, 4.2))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 4.2)
    ax.axis("off")
    boxes = [
        (10.4, "۱. داده‌ی بانک", "۱۴ جدول عملیاتی\nبیش از ۲۵۰ میلیون رکورد", LIGHT, BLUE),
        (7.0, "۲. یکپارچه‌سازی", "۱۲ نمای SQL: حذف تکرار،\nیکسان‌سازی قالب‌ها،\nاعمال کلید طبیعی", "#BDD7EE", BLUE),
        (3.6, "۳. تحلیل", "اسکریپت‌های تحلیلی:\nجدول‌ها و نمودارهای\nهر فصل", "#9DC3E6", BLUE),
        (0.2, "۴. گزارش", "جدول‌ها، نمودارها،\nشاخص‌های کلیدی و\nپیوست‌ها", BLUE, "white"),
    ]
    for x, head, body, fc, tc in boxes:
        ax.add_patch(FancyBboxPatch((x, 1.5), 2.4, 2.0, boxstyle="round,pad=0.05,rounding_size=0.15",
                                    fc=fc, ec=BLUE, lw=1.4))
        ax.text(x + 1.2, 3.1, head, ha="center", va="center", fontsize=13, color=tc, fontweight="bold")
        ax.text(x + 1.2, 2.25, body, ha="center", va="center", fontsize=10.5, color=tc, linespacing=1.5)
    for x in (2.7, 6.1, 9.5):
        ax.annotate("", xy=(x, 2.5), xytext=(x + 0.8, 2.5),
                    arrowprops=dict(arrowstyle="-|>", color=GREY, lw=1.8))
    ax.add_patch(FancyBboxPatch((1.2, 0.15), 5.8, 0.8, boxstyle="round,pad=0.05,rounding_size=0.15",
                                fc="#FCE4D6", ec=ORANGE, lw=1.3))
    ax.text(4.1, 0.55, "آمار ماهانه‌ی رسمی بانک (استان و شعبه، ۶۰ ماه) برای کالیبراسیون و تطبیق ارقام",
            ha="center", va="center", fontsize=10.5, color="#7F3F0F")
    ax.annotate("", xy=(4.8, 1.5), xytext=(4.5, 0.98), arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=1.5))
    save(fig, "ch1_data_pipeline.png")


def fig_timeline() -> None:
    rows = [
        ("فعالیت ماهانه‌ی سپرده", 1399.0, 1405.0, "core"),
        ("مانده‌ی ماهانه‌ی تسهیلات", 1400.0, 1405.0, "core"),
        ("سود پرداختی سپرده", 1400.0, 1405.0, "core"),
        ("اقساط و عملکرد بازپرداخت", 1399.0, 1405.25, "extra"),
        ("اطلاعات قرارداد تسهیلات (تاریخ اعطا)", 1399.0, 1405.0, "core"),
        ("خلاصه‌ی ماهانه‌ی کارمزد و گردش مشتری", 1399.0, 1405.0, "extra"),
        ("آمار رسمی ماهانه‌ی استان و شعب", 1400.0, 1405.0, "official"),
    ]
    colors = {"core": BLUE, "extra": "#9DC3E6", "official": ORANGE}
    fig, ax = plt.subplots(figsize=(12, 4.6))
    ax.axvspan(1400.0, 1405.0, color="#FFF2CC", alpha=0.7, zorder=0)
    for i, (lab, a, b, kind) in enumerate(rows[::-1]):
        ax.barh(i, b - a, left=a, color=colors[kind], height=0.5, zorder=2)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows][::-1])
    ticks = [1399 + k for k in range(7)]
    ax.set_xticks(ticks)
    ax.set_xticklabels([pd_(f"01/{t}") for t in ticks], fontsize=10)
    ax.set_xlim(1398.9, 1405.4)
    ax.text(1402.5, len(rows) - 0.1, "بازه‌ی توافق‌شده‌ی تحلیل: " + pd_("01/1400") + " تا " + pd_("12/1404"),
            ha="center", va="center", color="#7F6000", fontsize=11)
    ax.set_xlabel("آغاز سال (ماه/سال)")
    ax.set_ylim(-0.6, len(rows) + 0.2)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in colors.values()]
    ax.legend(handles, ["داده‌ی اصلی تحلیل", "داده‌ی تکمیلی", "آمار رسمی بانک"], loc="lower left", frameon=False, ncol=3, fontsize=10,
              bbox_to_anchor=(0, -0.3))
    save(fig, "ch2_data_timeline.png")


def fig_share_count_vs_value() -> None:
    cov = pd.read_csv(PROC_DIR / "bank_coverage_monthly.csv")
    last = cov[cov.year_month == 140412].iloc[0]
    groups = ["سپرده‌گذاران", "تسهیلات‌گیرندگان"]
    by_count = [706_509 / 7_404_240 * 100, 249_708 / 1_583_168 * 100]
    by_value = [last.deposit_coverage_pct, last.loan_coverage_pct]
    x = np.arange(2)
    w = 0.34
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    b1 = ax.bar(x - w / 2, by_count, w, color="#9DC3E6", label="سهم از تعداد مشتریان بانک")
    b2 = ax.bar(x + w / 2, by_value, w, color=BLUE, label="سهم از مبلغ کل بانک (اسفند ۱۴۰۴)")
    for bars in (b1, b2):
        for r in bars:
            ax.text(r.get_x() + r.get_width() / 2, r.get_height() + 1.5, pd_(f"{r.get_height():.1f}") + "٪", ha="center", fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(groups, fontsize=12)
    ax.set_ylim(0, 105)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: pd_(f"{v:.0f}") + "٪"))
    ax.set_ylabel("سهم نمونه از کل بانک")
    ax.legend(frameon=False, loc="upper left", fontsize=10.5)
    save(fig, "ch2_share_count_vs_value.png")


def fig_coverage_trend() -> None:
    d = pd.read_csv(PROC_DIR / "bank_coverage_monthly.csv")
    d["dep"] = d.deposit_coverage_pct.where(d.deposit_coverage_reliable)
    d["npl"] = d.npl_coverage_pct.where(d.npl_coverage_reliable)
    idx = np.arange(len(d))
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(idx, d.loan_coverage_pct, color=BLUE, lw=2.2, label="تسهیلات")
    ax.plot(idx, d.dep, color=GREEN, lw=2.2, label="منابع ریالی (سپرده)")
    ax.plot(idx, d.npl, color=ORANGE, lw=2.0, ls="--", label="مطالبات غیرجاری")
    ticks = [i for i in range(0, 60, 6)] + [59]
    ax.set_xticks(ticks)
    ax.set_xticklabels([ym_label(d.year_month[i]) for i in ticks], fontsize=9.5, rotation=0)
    ax.set_ylim(40, 100)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: pd_(f"{v:.0f}") + "٪"))
    ax.set_ylabel("سهم نمونه از کل بانک (بر حسب مبلغ)")
    ax.grid(axis="y", color="#E5E5E5")
    for col, c, dy in (("loan_coverage_pct", BLUE, 2.0), ("dep", GREEN, -4.5), ("npl", ORANGE, 2.0)):
        v = d[col].iloc[-1]
        ax.text(59.3, v + dy * 0.2, pd_(f"{v:.1f}") + "٪", color=c, fontsize=10.5, va="center")
    ax.set_xlim(-1, 63)
    ax.legend(frameon=False, loc="lower left", ncol=3, fontsize=10.5)
    save(fig, "ch2_coverage_trend.png")


def fig_npl_sample_vs_bank() -> None:
    d = pd.read_csv(PROC_DIR / "bank_coverage_monthly.csv")
    d["bank_ratio"] = (d.bank_npl / d.bank_loans * 100).where(d.npl_coverage_reliable)
    d["sample_ratio"] = (d.sample_npl / d.sample_loans * 100).where(d.npl_coverage_reliable)
    r = d[["bank_ratio", "sample_ratio"]].corr().iloc[0, 1]
    idx = np.arange(len(d))
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(idx, d.bank_ratio, color=BLUE, lw=2.4, label="کل بانک (آمار رسمی)")
    ax.plot(idx, d.sample_ratio, color=ORANGE, lw=2.0, ls="--", label="نمونه‌ی تحلیلی")
    ticks = [i for i in range(0, 60, 6)] + [59]
    ax.set_xticks(ticks)
    ax.set_xticklabels([ym_label(d.year_month[i]) for i in ticks], fontsize=9.5)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: pd_(f"{v:.0f}") + "٪"))
    ax.set_ylim(0, 11)
    ax.set_ylabel("نسبت مطالبات غیرجاری به کل تسهیلات")
    ax.grid(axis="y", color="#E5E5E5")
    ax.text(0.01, 0.95, "ضریب همبستگی دو سری: " + pd_(f"{r:.2f}"), transform=ax.transAxes, fontsize=11, color=BLUE, va="top")
    ax.legend(frameon=False, loc="upper center", ncol=2, fontsize=10.5)
    save(fig, "ch2_npl_sample_vs_bank.png")
    print("NPL ratio correlation", round(r, 4))


def fig_loan_band_rate() -> None:
    d = pd.read_csv(PROC_DIR / "loan_band_sample_vs_bank.csv")
    rate = d.sample_to_bank_ratio * 100
    fig, ax = plt.subplots(figsize=(11, 5.2))
    x = np.arange(len(d))
    cols = [LIGHT if r < 50 else "#8FAADC" if r < 90 else BLUE for r in rate]
    ax.bar(x, rate, color=cols, width=0.6)
    ax.axhline(100, color=ORANGE, ls="--", lw=1.4)
    ax.text(len(d) - 0.55, 103, "پوشش کامل (۱۰۰٪)", color=ORANGE, ha="right", fontsize=10)
    for i, (r, n_db, n_bank) in enumerate(zip(rate, d.db_customers, d.bank_total)):
        ax.text(i, (r + 3) if not 90 <= r <= 105 else 106, pd_(f"{r:.0f}") + "٪", ha="center", fontsize=12, color="#222222")
        if r >= 50:
            ax.text(i, 6, num(n_db) + "\nاز\n" + num(n_bank), ha="center", va="bottom", fontsize=9.5, color="white", linespacing=1.3)
        else:
            ax.text(i, r + 12, num(n_db) + " از " + num(n_bank), ha="center", va="bottom", fontsize=9.5, color="#333333")
    ax.set_xticks(x)
    ax.set_xticklabels(["کمتر از\n۵۰ میلیون", "۵۰ تا ۲۰۰\nمیلیون", "۲۰۰ میلیون\nتا ۱ میلیارد", "۱ تا ۵\nمیلیارد",
                        "۵ تا ۲۰\nمیلیارد", "بیش از\n۲۰ میلیارد"], fontsize=10)
    ax.set_ylim(0, 175)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: pd_(f"{v:.0f}") + "٪"))
    ax.set_ylabel("نسبت گیرندگان نمونه به کل گیرندگان بانک")
    ax.set_xlabel("طبقه‌ی میانگین مانده‌ی تسهیلات (۰۱/۱۴۰۴ تا ۰۹/۱۴۰۴)، تومان")
    save(fig, "ch2_sampling_rate_by_size.png")


def fig_tenure_mix() -> None:
    d = pd.read_csv(PROC_DIR / "tenure_sample_vs_bank.csv")
    bank = d.bank_total / d.bank_total.sum() * 100
    samp = d.db_customers / d.db_customers.sum() * 100
    y = np.arange(len(d))[::-1]
    h = 0.38
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    ax.barh(y + h / 2, bank, h, color="#9DC3E6", label="کل بانک")
    ax.barh(y - h / 2, samp, h, color=BLUE, label="نمونه‌ی تحلیلی")
    for yy, b, s_ in zip(y, bank, samp):
        ax.text(b + 0.6, yy + h / 2, pd_(f"{b:.1f}") + "٪", va="center", fontsize=9.5)
        ax.text(s_ + 0.6, yy - h / 2, pd_(f"{s_:.1f}") + "٪", va="center", fontsize=9.5)
    ax.set_yticks(y)
    ax.set_yticklabels(d.band, fontsize=10.5)
    ax.set_xlim(0, 48)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: pd_(f"{v:.0f}") + "٪"))
    ax.set_xlabel("سهم از کل مشتریان")
    ax.legend(frameon=False, loc="lower right", fontsize=10.5)
    save(fig, "ch2_tenure_mix.png")


def fig_filter_compliance() -> None:
    c = pd.read_csv(PROC_DIR / "sampling_filter_compliance.csv")
    r = c[c.evaluation.str.contains("اسفند")].iloc[0]
    items = [("هر چهار معیار هم‌زمان", r.all_four), ("تازگی (تراکنش در شش ماه اخیر)", r.recency),
             ("تکرار (حداقل یک ماه فعال)", r.frequency), ("ارزش پولی (مانده ≥ ۵۰۰ هزار تومان)", r.monetary),
             ("قدمت (حداقل ۱۲ ماه)", r.tenure)]
    fig, ax = plt.subplots(figsize=(9.5, 4.2))
    y = np.arange(len(items))[::-1]
    vals = [v / r.depositors * 100 for _, v in items]
    ax.barh(y, vals, color=[BLUE] + ["#9DC3E6"] * 4, height=0.55)
    for yy, v in zip(y, vals):
        ax.text(v + 0.6, yy, pd_(f"{v:.1f}") + "٪", va="center", fontsize=11)
    ax.set_yticks(y)
    ax.set_yticklabels([i[0] for i in items], fontsize=10.5)
    ax.set_xlim(0, 112)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: pd_(f"{v:.0f}") + "٪"))
    ax.set_xlabel("سهم از سپرده‌گذاران نمونه (۱۲/۱۴۰۴)")
    save(fig, "ch3_filter_compliance.png")


def fig_customer_overlap() -> None:
    from matplotlib_venn import venn2
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    v = venn2(subsets=(456_835, 34, 249_674), set_labels=("", ""), ax=ax, set_colors=(BLUE, ORANGE), alpha=0.55)
    for idx, txt in (("10", "فقط سپرده‌گذار\n" + num(456_835) + "\n(" + pd_("64.7") + "٪)"),
                     ("11", "سپرده‌گذار و گیرنده‌ی اصلی\n" + num(249_674) + "\n(" + pd_("35.3") + "٪)")):
        lab = v.get_label_by_id(idx)
        lab.set_text(txt)
        lab.set_fontsize(11)
        lab.set_color("white" if idx == "10" else "#222222")
    if v.get_label_by_id("01"):
        v.get_label_by_id("01").set_text("")
    ax.text(-0.62, 0.62, "سپرده‌گذاران: " + num(706_509), color=BLUE, fontsize=11.5, ha="center")
    ax.text(0.62, 0.52, "گیرندگان اصلی: " + num(249_708), color=ORANGE, fontsize=11.5, ha="center")
    ax.text(0, -0.62, "فقط گیرنده‌ی اصلی (بدون سپرده): " + num(34) + " نفر", ha="center", fontsize=10, color=GREY)
    save(fig, "ch3_customer_overlap.png")


def fig_cohort() -> None:
    d = pd.read_csv(PROC_DIR / "deposit_cohort_retention.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.5, 4.8), gridspec_kw={"width_ratios": [1, 1.25]})
    x = np.arange(len(d))
    a1.bar(x, d.cohort_size, color="#9DC3E6", width=0.6)
    for i, n in enumerate(d.cohort_size):
        a1.text(i, n + 1200, num(n), ha="center", fontsize=9.5)
    a1.set_xticks(x)
    a1.set_xticklabels([pd_(str(y)) for y in d.cohort_year])
    a1.set_ylabel("تعداد مشتریان کوهورت")
    a1.yaxis.set_major_formatter(FuncFormatter(lambda v, _: num(v)))
    a1.set_xlabel("سال افتتاح اولین حساب سپرده")
    a1.set_title("اندازه‌ی کوهورت‌ها", fontsize=12, color=BLUE)
    ok = d[d.cohort_year < 1404]
    a2.bar(np.arange(len(ok)), ok.retention_pct, color=BLUE, width=0.6)
    for i, r in enumerate(ok.retention_pct):
        a2.text(i, r + 0.4, pd_(f"{r:.1f}") + "٪", ha="center", fontsize=11)
    a2.bar([len(ok)], [100], bottom=0, color="white", edgecolor=GREY, hatch="//", width=0.6)
    a2.text(len(ok), 80, "قابل\nمحاسبه\nنیست", ha="center", va="center", fontsize=10.5, color="#333333",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.9))
    a2.set_xticks(np.arange(len(d)))
    a2.set_xticklabels([pd_(str(y)) for y in d.cohort_year])
    a2.set_ylim(60, 101)
    a2.yaxis.set_major_formatter(FuncFormatter(lambda v, _: pd_(f"{v:.0f}") + "٪"))
    a2.set_ylabel("درصد مشتریان فعال در ۱۲/۱۴۰۴")
    a2.set_xlabel("سال افتتاح اولین حساب سپرده")
    a2.set_title("نرخ ماندگاری کوهورت‌ها", fontsize=12, color=BLUE)
    save(fig, "ch3_cohort_retention.png")


def fig_churn() -> None:
    d = pd.read_csv(PROC_DIR / "deposit_annual_churn_rate.csv")
    labels = [pd_(f"{a} تا {b}") for a, b in zip(d.from_year, d.to_year)]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.5, 4.6))
    x = np.arange(len(d))
    rate = 100 * d.churned_customers / d.active_customers_start  # نرخ دقیق (CSV یک‌رقمی گرد شده است)
    a1.bar(x, rate, color=BLUE, width=0.6)
    for i, (r, n) in enumerate(zip(rate, d.churned_customers)):
        a1.text(i, r + 0.015, pd_(f"{r:.2f}") + "٪\n" + num(n) + " نفر", ha="center", fontsize=9.5)
    a1.set_xticks(x)
    a1.set_xticklabels(labels, fontsize=9.5)
    a1.set_ylim(0, 0.8)
    a1.yaxis.set_major_formatter(FuncFormatter(lambda v, _: pd_(f"{v:.2f}") + "٪"))
    a1.set_title("نرخ ریزش سالانه‌ی سپرده‌گذاران (تعدادی)", fontsize=12, color=BLUE)
    a1.set_xlabel("گذار سالانه")
    a2.bar(x, d.churned_balance_share_pct, color=ORANGE, width=0.6)
    for i, r in enumerate(d.churned_balance_share_pct):
        a2.text(i, r + 0.015, pd_(f"{r:.2f}") + "٪", ha="center", fontsize=10)
    a2.set_xticks(x)
    a2.set_xticklabels(labels, fontsize=9.5)
    a2.set_ylim(0, 1.0)
    a2.yaxis.set_major_formatter(FuncFormatter(lambda v, _: pd_(f"{v:.2f}") + "٪"))
    a2.set_title("سهم مانده‌ی ازدست‌رفته از کل مانده‌ی ابتدای دوره", fontsize=12, color=ORANGE)
    a2.set_xlabel("گذار سالانه")
    save(fig, "ch3_annual_churn.png")


def fig_deposit_only_profile() -> None:
    d = pd.read_csv(PROC_DIR / "deposit_balance_by_relationship.csv")
    g = d[d.group == "فقط سپرده‌گذار"].reset_index(drop=True)
    cust = g.customers / g.customers.sum() * 100
    bal = g.balance / g.balance.sum() * 100
    x = np.arange(len(g))
    w = 0.38
    fig, ax = plt.subplots(figsize=(11.5, 5.2))
    ax.bar(x - w / 2, cust, w, color="#9DC3E6", label="سهم از تعداد مشتریان")
    ax.bar(x + w / 2, bal, w, color=BLUE, label="سهم از مانده‌ی سپرده")
    for i, (c, b) in enumerate(zip(cust, bal)):
        ax.text(i - w / 2, c + 1.2, pd_(f"{c:.1f}") + "٪", ha="center", fontsize=9.5)
        ax.text(i + w / 2, b + 1.2, pd_(f"{b:.1f}") + "٪", ha="center", fontsize=9.5)
    ax.set_xticks(x)
    ax.set_xticklabels(["کمتر از\u200c۰.۵", "۰.۵ تا ۲.۵", "۲.۵ تا ۱۰", "۱۰ تا ۵۰", "۵۰ تا ۲۰۰", "۲۰۰ تا ۱۰۰۰", "بیش از ۱۰۰۰"], fontsize=10)
    ax.set_xlabel("طبقه‌ی مانده‌ی سپرده‌گذار (میلیون تومان، ۱۲/۱۴۰۴)")
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: pd_(f"{v:.0f}") + "٪"))
    ax.set_ylabel("سهم از گروه (درصد)")
    ax.legend(frameon=False, loc="upper center", fontsize=10.5)
    save(fig, "ch3_deposit_only_profile.png")


if __name__ == "__main__":
    fig_sampling_funnel()
    fig_pipeline()
    fig_timeline()
    fig_share_count_vs_value()
    fig_coverage_trend()
    fig_npl_sample_vs_bank()
    fig_loan_band_rate()
    fig_tenure_mix()
    fig_filter_compliance()
    fig_customer_overlap()
    fig_cohort()
    fig_churn()
    fig_deposit_only_profile()
