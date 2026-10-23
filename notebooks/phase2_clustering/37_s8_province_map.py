"""فاز ۲ - S8 (تکمیل): نقشه‌ی استانی نمایه‌های نمونه از GeoJSON استان‌ها (matplotlib، بدون geopandas).
ورودی: s8_province_indicators.csv، data/raw/geo/iran_provinces.geojson. خروجی: reports/figures/phase2_clustering/ch8_province_maps.png"""
import json
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.collections import PatchCollection
from tt_bank.common.persian_plot import FONTS_DIR, setup_persian_font, to_persian_digits
ROOT = Path(__file__).resolve().parents[2]; D = ROOT / "data" / "processed" / "phase2_clustering"; FIG = ROOT / "reports" / "figures" / "phase2_clustering"
setup_persian_font(); fd = to_persian_digits
FA = {"Tehran": "تهران", "Alborz": "البرز", "Qazvin": "قزوین", "Qom": "قم", "Markazi": "مرکزی", "Isfahan": "اصفهان", "Fars": "فارس", "Khuzestan": "خوزستان", "Kohgiluyeh and Boyer-Ahmad": "کهگیلویه و بویراحمد",
      "Bushehr": "بوشهر", "Hormozgan": "هرمزگان", "Kerman": "کرمان", "Sistan and Baluchestan": "سیستان و بلوچستان", "Yazd": "یزد", "South Khorasan": "خراسان جنوبی", "Razavi Khorasan": "خراسان رضوی",
      "North Khorasan": "خراسان شمالی", "Semnan": "سمنان", "Golestan": "گلستان", "Mazandaran": "مازندران", "Gilan": "گیلان", "Ardabil": "اردبیل", "East Azerbaijan": "آذربایجان شرقی",
      "West Azerbaijan": "آذربایجان غربی", "Zanjan": "زنجان", "Kurdistan": "کردستان", "Kermanshah": "کرمانشاه", "Ilam": "ایلام", "Lorestan": "لرستان", "Hamadan": "همدان", "Chaharmahal and Bakhtiari": "چهارمحال و بختیاری"}
key = lambda s: s.replace(" ", "").replace("\u200c", "").replace("ي", "ی").replace("ك", "ک")
J = pd.read_csv(D / "s8_province_indicators.csv", index_col=0); J.index = [key(i) for i in J.index]
g = json.load(open(ROOT / "data" / "raw" / "geo" / "iran_provinces.geojson", encoding="utf-8"))
def polys(geom):
    if geom["type"] == "Polygon": return [geom["coordinates"]]
    return geom["coordinates"]
panels = [("share_T", "سهم گروه T از مشتریان استان (٪)", "Oranges"), ("share_C1S", "سهم C1 و S از مشتریان استان (٪)", "Blues"), ("npl_ratio", "نسبت غیرجاری نمونه (٪)", "Reds")]
fig, axs = plt.subplots(1, 3, figsize=(16, 5.6)); miss = set()
for ax, (col, title, cmap) in zip(axs, panels):
    vals = {}; patches = []; v = []
    for f in g["features"]:
        nm = FA.get(f["properties"]["shapeName"]); k = key(nm) if nm else None
        if k is None or k not in J.index: miss.add(f["properties"]["shapeName"]); continue
        for poly in polys(f["geometry"]):
            patches.append(MplPolygon(np.array(poly[0]), closed=True)); v.append(J.loc[k, col])
    pc = PatchCollection(patches, cmap=cmap, edgecolor="white", linewidth=.5); pc.set_array(np.array(v)); ax.add_collection(pc)
    ax.autoscale_view(); ax.set_aspect("equal"); ax.axis("off"); ax.set_title(title, fontsize=11)
    cb = fig.colorbar(pc, ax=ax, shrink=.7); cb.ax.set_yticklabels([fd(f"{t:g}") for t in cb.get_ticks()]); 
fig.savefig(FIG / "ch8_province_maps.png", bbox_inches="tight", facecolor="white", dpi=200); print("saved; بدون داده:", miss)
