"""فهرست نهایی نمودارها و جدول‌های گزارش فاز ۲، برگه‌ی نمایش (contact sheet) و فایل واحد جدول‌ها (reports/phase2_tables.md)."""
import re
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt, matplotlib.image as mpimg
from tt_bank.common.persian_plot import to_persian_digits as fd

ROOT = Path(__file__).resolve().parents[2]; FIG = ROOT / "reports" / "figures" / "phase2_final"; TAB = ROOT / "reports" / "tables_phase2"
CH = {"0": "خلاصه‌ی مدیریتی", "1": "فصل ۱: مقدمه و داده", "2": "فصل ۲: مرور روش‌های خوشه‌بندی", "3": "فصل ۳: ویژگی‌ها، آماده‌سازی و انتخاب مدل", "4": "فصل ۴: خوشه‌های نهایی و نمای سپرده", "5": "فصل ۵: ارزش اقتصادی و ریسک",
      "6": "فصل ۶: پویایی مشتریان", "7": "فصل ۷: جغرافیا و شعب", "8": "فصل ۸: برآورد برای کل بانک"}
figs = sorted([p for p in FIG.glob("f*.png")], key=lambda p: tuple(int(x) for x in re.match(r"f(\d+)_(\d+)_", p.name).groups()))
tabs = sorted([p for p in TAB.glob("t*.md")], key=lambda p: tuple(int(x) for x in re.match(r"t(\d+)_(\d+)_", p.name).groups()) if re.match(r"t(\d+)_(\d+)_", p.name) else (99, 0))

# فهرست
lines = ["# فهرست نمودارها و جدول‌های گزارش نهایی فاز ۲", "", f"نمودارها: {len(figs)} فایل در `reports/figures/phase2_final/`؛ جدول‌ها: {len(tabs)} فایل در `reports/tables_phase2/` (CSV عددی و مارک‌داون با ارقام فارسی)؛ همه‌ی جدول‌ها در `reports/phase2_tables.md`.", "", "## نمودارها", "", "| شماره | فایل | فصل |", "|---|---|---|"]
for p in figs:
    c, n = re.match(r"f(\d+)_(\d+)_", p.name).groups(); lines.append(f"| شکل {fd(c)}-{fd(n)} | `{p.name}` | {CH[c]} |")
lines += ["", "## جدول‌ها", "", "| شماره | فایل | عنوان |", "|---|---|---|"]
alltab = []
for p in tabs:
    txt = p.read_text(encoding="utf-8"); cap = re.match(r"\*\*(.+?)\*\*", txt).group(1); lines.append(f"| {cap.split(':')[0]} | `{p.name}` | {cap.split(':', 1)[1].strip()} |"); alltab.append(txt)
(ROOT / "reports" / "phase2_assets_manifest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
(ROOT / "reports" / "phase2_tables.md").write_text("# جدول‌های گزارش نهایی فاز ۲\n\n" + "\n\n".join(alltab), encoding="utf-8")

# برگه‌ی نمایش
per = 12
for k in range(0, len(figs), per):
    chunk = figs[k:k + per]; fig, axs = plt.subplots(4, 3, figsize=(15, 13))
    for ax in axs.ravel(): ax.axis("off")
    for ax, p in zip(axs.ravel(), chunk): ax.imshow(mpimg.imread(p)); ax.set_title(p.stem, fontsize=9, pad=3)
    fig.tight_layout(); fig.savefig(FIG / f"_contact_sheet_{k // per + 1}.png", dpi=110, facecolor="white"); plt.close(fig)
print(len(figs), "figures;", len(tabs), "tables")
