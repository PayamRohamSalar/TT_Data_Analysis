"""فاز ۲ - S5b: نمودارهای لنزهای سپرده و اعتبار (از CSV)."""
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter, ScalarFormatter
from tt_bank.common.persian_plot import FONTS_DIR, setup_persian_font, to_persian_digits
ROOT = Path(__file__).resolve().parents[2]; D = ROOT / "data" / "processed" / "phase2_clustering"; FIG = ROOT / "reports" / "figures" / "phase2_clustering"
setup_persian_font(); font_manager.fontManager.addfont(str(FONTS_DIR / "Vazirmatn-Bold.ttf"))
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 11, "savefig.dpi": 200, "axes.grid": True, "grid.color": "#E6E6E6", "axes.axisbelow": True})
fd = to_persian_digits; BLUE, ORANGE, GREEN, RED = "#1F4E79", "#C55A11", "#548235", "#B03A2E"
def save(fig, name):
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            f = axis.get_major_formatter()
            if isinstance(f, ScalarFormatter): axis.set_major_formatter(FuncFormatter(lambda v, pos: fd(f"{v:g}")))
    fig.savefig(FIG / name, bbox_inches="tight", facecolor="white"); plt.close(fig); print("saved", name)
d = pd.read_csv(D / "s5b_deposit_lens_profile.csv"); c = pd.read_csv(D / "s5b_credit_lens_v2_profile.csv")
fig, ax = plt.subplots(figsize=(9, 4.6)); x = np.arange(len(d)); w = .27
ax.bar(x - w, d.share_customers * 100, w, color=BLUE, label="سهم مشتریان"); ax.bar(x, d.deposit_share * 100, w, color=ORANGE, label="سهم مانده‌ی سپرده"); ax.bar(x + w, d.loan_share * 100, w, color=GREEN, label="سهم مانده‌ی تسهیلات")
ax.set_xticks(x); ax.set_xticklabels([fd(int(i)) for i in d.lens]); ax.set_xlabel("خوشه‌ی لنز سپرده"); ax.set_ylabel("درصد"); ax.legend(frameon=False); ax.grid(axis="x", visible=False); save(fig, "ch5_deposit_lens.png")
fig, ax = plt.subplots(figsize=(9, 4.6)); x = np.arange(len(c))
ax.bar(x - w, c.share_borrowers * 100, w, color=BLUE, label="سهم وام‌گیران"); ax.bar(x, c.loan_share * 100, w, color=GREEN, label="سهم مانده‌ی تسهیلات"); ax.bar(x + w, c.npl_share_of_total * 100, w, color=RED, label="سهم مانده‌ی غیرجاری")
ax.set_xticks(x); ax.set_xticklabels([fd(int(i)) for i in c.lens]); ax.set_xlabel("خوشه‌ی لنز اعتبار"); ax.set_ylabel("درصد"); ax.legend(frameon=False); ax.grid(axis="x", visible=False); save(fig, "ch5_credit_lens.png")
