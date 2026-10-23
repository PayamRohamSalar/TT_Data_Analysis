"""فاز ۲ - تکمیل نمودارهای وعده‌داده‌شده در طرح (فصل‌های 1، 2، 4، 5، 7) پس از داوری دور سوم؛ بدون DB.
ن 1-1 قیف جمعیت، ن 2-1 مشتری در هر ماه، ن 2-2 ماه‌های حضور، ن 2-3 ورود به تفکیک سال، ن 2-4 ترکیب رابطه، ن 4-6 نمایش PCA، ن 5-6 ترکیب نوع وام، ن 7-4 مسیرهای برتر، ن 7-5 مهاجرت به گیرنده‌ی اصلی.
خروجی: reports/figures/phase2_clustering/ch{1,2,4,5,7}_*.png و s10b_*.csv"""
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter, ScalarFormatter
from sklearn.decomposition import PCA
from tt_bank.common.persian_plot import FONTS_DIR, setup_persian_font, to_persian_digits
from tt_bank.phase2_clustering.prep import Prep

ROOT = Path(__file__).resolve().parents[2]; D = ROOT / "data" / "processed" / "phase2_clustering"; FIG = ROOT / "reports" / "figures" / "phase2_clustering"
setup_persian_font(); font_manager.fontManager.addfont(str(FONTS_DIR / "Vazirmatn-Bold.ttf"))
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 11, "savefig.dpi": 200, "axes.grid": True, "grid.color": "#E6E6E6", "axes.axisbelow": True})
fd = to_persian_digits; BLUE, ORANGE, GREEN, RED, GREY = "#1F4E79", "#C55A11", "#548235", "#B03A2E", "#7F7F7F"
def save(fig, name):
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            f = axis.get_major_formatter()
            if isinstance(f, ScalarFormatter): axis.set_major_formatter(FuncFormatter(lambda v, pos: fd(f"{v:g}")))
    fig.savefig(FIG / name, bbox_inches="tight", facecolor="white"); plt.close(fig); print("saved", name)
SEG = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "T", "I", "N", "S"]
mfmt = FuncFormatter(lambda v, p: fd(f"{v / 1e3:g}") + " هزار" if v < 1e6 else fd(f"{v / 1e6:g}") + " میلیون")

# ن 1-1 قیف جمعیت 1404
d = pd.read_csv(D / "cluster_definitions.csv"); cnt = d.set_index("segment").customers_1404
cs = cnt[["C%d" % i for i in range(1, 9)]].sum()
steps = [("مشتریان با ردیف در 1404", cnt.sum()), ("پس از کنار گذاشتن نهادی (S)", cnt.sum() - cnt["S"]), ("پس از کنار گذاشتن نوپا (N)", cnt.sum() - cnt["S"] - cnt["N"]),
         ("پس از کنار گذاشتن بی‌فعالیت/نمادین (I)", cnt.sum() - cnt["S"] - cnt["N"] - cnt["I"]), ("گروه مدل (C1 تا C8 و T)", cs + cnt["T"]), ("خوشه‌بندی اصلی (پس از جدا کردن T)", cs)]
fig, ax = plt.subplots(figsize=(9, 4.4)); y = np.arange(len(steps))[::-1]
ax.barh(y, [s[1] for s in steps], color=BLUE, height=.6); ax.set_yticks(y); ax.set_yticklabels([fd(s[0]) for s in steps]); ax.xaxis.set_major_formatter(mfmt); ax.set_xlabel("تعداد مشتری"); ax.grid(axis="y", visible=False)
for yi, s in zip(y, steps): ax.text(s[1], yi, " " + fd(f"{int(s[1]):,}"), va="center", fontsize=9)
ax.set_xlim(0, steps[0][1] * 1.18); save(fig, "ch1_population_funnel.png")

# ن 2-1 مشتری در هر ماه
m = pd.read_csv(D / "customers_by_month.csv"); m["t"] = np.arange(len(m)); lab = [i for i in range(len(m)) if m.ym[i] % 100 == 1]
fig, ax = plt.subplots(figsize=(10, 4.4)); ax.plot(m.t, m.customers, color=BLUE, label="مشتری دارای ردیف"); ax.plot(m.t, m.turn, color=ORANGE, label="مشتری دارای گردش")
ax.set_xticks(lab); ax.set_xticklabels([fd(f"01/{m.ym[i] // 100}") for i in lab], fontsize=9); ax.yaxis.set_major_formatter(mfmt); ax.legend(frameon=False); ax.set_ylabel("تعداد مشتری")
save(fig, "ch2_customers_by_month.png")

# ن 2-2 ماه‌های حضور و گردش (1404)
F = pd.read_pickle(D / "features_customer_year.pkl"); G = F[F.y == 1404]
fig, ax = plt.subplots(figsize=(9, 4.2)); w = .4; k = np.arange(1, 13)
ax.bar(k - w / 2, G.months.clip(1, 12).value_counts().reindex(k).fillna(0), w, color=BLUE, label="ماه‌های حضور"); ax.bar(k + w / 2, G.turn_months.clip(0, 12).value_counts().reindex(k).fillna(0), w, color=ORANGE, label="ماه‌های دارای گردش")
ax.set_xticks(k); ax.yaxis.set_major_formatter(mfmt); ax.legend(frameon=False); ax.set_xlabel("تعداد ماه در 1404"); ax.set_ylabel("تعداد مشتری"); ax.grid(axis="x", visible=False); save(fig, "ch2_months_distribution.png")

# ن 2-3 ورود به تفکیک سال نخستین ردیف
e = pd.read_csv(D / "entry_first_month_72m.csv"); e["year"] = e["first"] // 100; ey = e.groupby("year")["count"].sum(); ey.to_csv(D / "s10b_entries_by_year.csv")
fig, ax = plt.subplots(figsize=(8.4, 4.2)); ax.bar([fd(str(i)) for i in ey.index], ey.values, color=BLUE, width=.6); ax.yaxis.set_major_formatter(mfmt); ax.set_ylabel("تعداد مشتری (نخستین ردیف)"); ax.grid(axis="x", visible=False)
ax.set_xlabel("سال نخستین ردیف (1399: مشتریان آغازین پایگاه)"); save(fig, "ch2_entries_by_year.png")

# ن 2-4 ترکیب رابطه
r = pd.read_csv(D / "s1_relationship_by_year.csv").set_index("y"); names = {"deposit_only": "فقط سپرده", "party_only": "فقط ضامن/شریک", "primary_inferred": "گیرنده‌ی اصلی استنتاجی", "primary_record": "گیرنده‌ی اصلی قراردادی"}
fig, ax = plt.subplots(figsize=(8.6, 4.4)); bot = np.zeros(len(r))
for c, col in zip(names, [GREY, ORANGE, GREEN, BLUE]):
    ax.bar([fd(str(i)) for i in r.index], r[c] / r.total * 100, bottom=bot, color=col, label=names[c], width=.6); bot += (r[c] / r.total * 100).to_numpy()
ax.set_ylabel("درصد مشتریان"); ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(.5, -.1), ncol=2); ax.grid(axis="x", visible=False); save(fig, "ch2_relationship_by_year.png")

# ن 5-6 ترکیب نوع عقد در خوشه‌های وام‌گیر
P = pd.read_csv(D / "cluster_profiles.csv").set_index("segment"); bs = ["C1", "C2", "C3", "C4", "C6", "C7", "C8", "T", "N", "S"]
q, mu, ins = P.loc[bs, "share_ltype_qard"], P.loc[bs, "share_ltype_murabaha"], P.loc[bs, "share_ltype_installment"]; oth = (1 - q - mu - ins).clip(lower=0)
fig, ax = plt.subplots(figsize=(9.4, 4.6)); bot = np.zeros(len(bs))
for v, col, lb in [(mu, BLUE, "مرابحه"), (q, GREEN, "قرض‌الحسنه"), (ins, ORANGE, "اقساطی"), (oth, GREY, "سایر")]:
    ax.bar(bs, v.to_numpy() * 100, bottom=bot, color=col, label=lb, width=.6); bot += v.to_numpy() * 100
ax.set_ylabel("درصد مانده‌ی وام (وزن‌دار)"); ax.legend(frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(.5, -.08)); ax.grid(axis="x", visible=False); save(fig, "ch5_loan_type_mix.png")

# ن 7-4 مسیرهای برتر
tp = pd.read_csv(D / "s7_top_paths.csv").head(10)[::-1]
fig, ax = plt.subplots(figsize=(8.8, 4.6)); ax.barh(range(len(tp)), tp.share * 100, color=BLUE, height=.6); ax.set_yticks(range(len(tp))); ax.set_yticklabels([p.replace(">", " ‹ ") for p in tp.path], fontsize=9)
ax.set_xlabel("سهم از " + fd("467,892") + " مشتری حاضر در هر پنج سال (٪)"); ax.grid(axis="y", visible=False); save(fig, "ch7_top_paths.png")

# ن 7-5 مهاجرت به گیرنده‌ی اصلی (از فقط سپرده یا ضامن)
A = pd.read_csv(D / "customer_cluster_assignments.csv.gz", usecols=["customer_id", "year", "segment", "relationship"], keep_default_na=False)
A = A.sort_values(["customer_id", "year"]); g = A.groupby("customer_id"); A["rel_next"] = g.relationship.shift(-1); A["yn"] = g.year.shift(-1)
B = A[(A.yn == A.year + 1) & A.relationship.isin(["deposit_only", "party_only"])].copy(); B["became_borrower"] = B.rel_next.isin(["primary_record", "primary_inferred"])
out = B.groupby("segment").agg(origin=("became_borrower", "size"), became_borrower=("became_borrower", "mean")).reindex(SEG).dropna(); out.to_csv(D / "s10b_deposit_to_borrower_by_segment.csv")
tot = B.became_borrower.mean(); print("کل گذار فقط‌سپرده/ضامن به گیرنده‌ی اصلی در سال بعد: %.4f (n=%d)" % (tot, len(B))); print(out.round(4).to_string())
fig, ax = plt.subplots(figsize=(9, 4.4)); ax.bar(out.index, out.became_borrower * 100, color=GREEN, width=.6); ax.axhline(tot * 100, color=GREY, ls="--")
ax.set_ylabel("درصد فقط‌سپرده/ضامن که سال بعد گیرنده‌ی اصلی شدند"); ax.grid(axis="x", visible=False); save(fig, "ch7_deposit_to_borrower.png")

# ن 4-6 نمایش PCA دوبعدی خوشه‌ها (زیرنمونه‌ی 40 هزارتایی)
seg = pd.read_pickle(D / "cluster_assignments_1404.pkl")[["customer_id", "segment"]]; Fm = G.merge(seg, on="customer_id"); Fm = Fm[Fm.segment.str.startswith("C")]
sub = Fm.sample(40000, random_state=20261030); prep = Prep.from_json(D / "prep_spec_v2.json"); X = prep.transform(sub)
pc = PCA(2, random_state=0).fit(X); Z = pc.transform(X); ev = pc.explained_variance_ratio_; print("PCA واریانس توضیح‌داده‌شده:", ev.round(3))
cols = dict(zip(["C%d" % i for i in range(1, 9)], plt.cm.tab10(np.arange(8))))
fig, ax = plt.subplots(figsize=(8.4, 6.4))
for s in cols:
    mk = (sub.segment == s).to_numpy(); ax.scatter(Z[mk, 0], Z[mk, 1], s=3, color=cols[s], alpha=.5, label=s)
ax.legend(markerscale=4, frameon=False, ncol=2); ax.set_xlabel("مؤلفه‌ی اول (" + fd(f"{ev[0] * 100:.0f}") + "٪ واریانس)"); ax.set_ylabel("مؤلفه‌ی دوم (" + fd(f"{ev[1] * 100:.0f}") + "٪ واریانس)"); save(fig, "ch4_pca_clusters.png")
