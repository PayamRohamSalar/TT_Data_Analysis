"""سبک مشترک نمودارها و جدول‌های گزارش نهایی فاز ۲ (پالت، فونت، ارقام فارسی، نام کوتاه خوشه‌ها، ذخیره‌ی جدول).
استفاده: from report_style import *   (اسکریپت‌های 40a تا 40c در همین پوشه‌اند)"""
from pathlib import Path
import re
import numpy as np, pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter, ScalarFormatter, FixedLocator
from tt_bank.common.persian_plot import FONTS_DIR, setup_persian_font, to_persian_digits

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data" / "processed" / "phase2_clustering"; P1 = ROOT / "data" / "processed" / "phase1_market_overview"
FIG = ROOT / "reports" / "figures" / "phase2_final"; TAB = ROOT / "reports" / "tables_phase2"
FIG.mkdir(parents=True, exist_ok=True); TAB.mkdir(parents=True, exist_ok=True)
setup_persian_font(); font_manager.fontManager.addfont(str(FONTS_DIR / "Vazirmatn-Bold.ttf"))
NAVY, ORANGE, GREEN, RED, GREY, TEAL, GOLD, PURPLE, LGREY = "#1F4E79", "#C55A11", "#548235", "#B03A2E", "#7F7F7F", "#2E8B8B", "#BF9000", "#7030A0", "#D9D9D9"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#808080", "font.size": 11, "axes.labelsize": 11, "axes.titlesize": 12,
                     "savefig.dpi": 220, "axes.grid": True, "grid.color": "#E6E6E6", "grid.linewidth": .8, "axes.axisbelow": True, "legend.frameon": False,
                     "axes.titleweight": "bold", "figure.facecolor": "white", "axes.unicode_minus": False})
fd = to_persian_digits
SEG = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "T", "I", "N", "S"]
CLR = {"C1": "#1F4E79", "C2": "#2E75B6", "C3": "#548235", "C4": "#7F7F7F", "C5": "#A9D18E", "C6": "#BF9000", "C7": "#B03A2E", "C8": "#ED7D31", "T": "#7030A0", "I": "#BFBFBF", "N": "#00B0F0", "S": "#262626"}
DEFS = pd.read_csv(D / "cluster_definitions.csv"); NAME = dict(zip(DEFS.segment, DEFS.name_fa))
LAB = {s: f"{NAME[s]} ({s})" for s in SEG}


def fd_safe(s):
    """ارقام فارسی، به‌جز کدهای لاتین مانند C1."""
    return "".join(p if re.fullmatch("[A-Za-z]+[0-9]*", p) else fd(p) for p in re.findall("[A-Za-z]+[0-9]*|[^A-Za-z]+", s))


def fnum(x, nd=0, pct=False):
    """قالب عدد فارسی با جداکننده‌ی هزارگان؛ pct=True علامت درصد."""
    if x is None or (isinstance(x, float) and np.isnan(x)): return "-"
    s = f"{x:,.{nd}f}"; return fd(s) + ("٪" if pct else "")


import re


def finish(fig, name, legend_below=False):
    """ارقام فارسی روی همه‌ی محورها (خطی)، ذخیره در reports/figures/phase2_final."""
    fig.canvas.draw()
    for ax in fig.axes:
        for axis, sc in ((ax.xaxis, ax.get_xscale()), (ax.yaxis, ax.get_yscale())):
            if sc != "linear": continue
            lab = [t.get_text() for t in axis.get_ticklabels()]
            if any(ch.isdigit() for l in lab for ch in l):
                locs = axis.get_ticklocs(); v0, v1 = sorted(axis.get_view_interval()); eps = (v1 - v0) * 1e-6
                keep = [(v0 - eps) <= q <= (v1 + eps) for q in locs]
                axis.set_ticks([q for q, k in zip(locs, keep) if k]); axis.set_ticklabels([(l if re.search("[A-Za-z]", l) else fd(l.replace("−", "-"))) for l, k in zip(lab, keep) if k])
    from matplotlib.text import Text
    RLM = chr(0x200F); NL = chr(10); fa_rng = "[" + chr(0x0600) + "-" + chr(0x06FF) + "]"
    mixed = lambda tx: bool(tx) and bool(re.search("[A-Za-z]", tx)) and bool(re.search(fa_rng, tx)) and not tx.startswith(RLM)
    fix = lambda tx: NL.join(RLM + q for q in tx.split(NL))
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            lab = [t.get_text() for t in axis.get_ticklabels()]
            if any(mixed(l) for l in lab):
                axis.set_ticks(axis.get_ticklocs()); axis.set_ticklabels([fix(l) if mixed(l) else l for l in lab])
    for t in fig.findobj(Text):
        tx = t.get_text()
        if mixed(tx): t.set_text(fix(tx))
    fig.savefig(FIG / name, bbox_inches="tight", facecolor="white"); plt.close(fig); print("saved", name)


def save_table(df, name, caption, nd=None, note=None):
    """جدول را به‌صورت CSV (عددی) و بلوک مارک‌داون (ارقام فارسی) ذخیره می‌کند؛ nd: دیکشنری ستون→رقم اعشار."""
    df.to_csv(TAB / f"{name}.csv", index=False, encoding="utf-8-sig")
    nd = nd or {}; out = df.copy()
    for c in out.columns:
        if pd.api.types.is_numeric_dtype(out[c]): out[c] = [fnum(v, nd.get(c, 0)) if pd.notna(v) else "-" for v in out[c]]
        else: out[c] = [fd_safe(str(v)) if pd.notna(v) else "-" for v in out[c]]
    md = f"**{caption}**\n\n| " + " | ".join(out.columns) + " |\n|" + "|".join(["---"] * len(out.columns)) + "|\n"
    for _, r in out.iterrows(): md += "| " + " | ".join(str(v) for v in r) + " |\n"
    if note: md += f"\n{note}\n"
    (TAB / f"{name}.md").write_text(md, encoding="utf-8"); print("table", name, df.shape)


def hbar_labels(ax, bars, vals, fmt=lambda v: fnum(v, 1), pad=.01):
    xmax = ax.get_xlim()[1]
    for b, v in zip(bars, vals): ax.text(b.get_width() + xmax * pad, b.get_y() + b.get_height() / 2, fmt(v), va="center", fontsize=9)


def box(ax, xy, w, h, text, fc="#EAF1F8", ec=NAVY, fs=10, bold=False, tc="black"):
    from matplotlib.patches import FancyBboxPatch
    ax.add_patch(FancyBboxPatch((xy[0] - w / 2, xy[1] - h / 2), w, h, boxstyle="round,pad=0.02,rounding_size=0.04", fc=fc, ec=ec, lw=1.2))
    ax.text(xy[0], xy[1], text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", color=tc, linespacing=1.5)


def arrow(ax, a, b, color=GREY):
    ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="-|>", color=color, lw=1.3, shrinkA=2, shrinkB=2))
