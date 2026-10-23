"""گزارش نهایی فاز ۲: نمودارها و جدول‌های فصل‌های 6 تا 8 و جدول ارقام کلیدی خلاصه‌ی مدیریتی."""
import json
from report_style import *
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.collections import PatchCollection

T6 = pd.read_csv(D / "s6_table_6_1.csv").set_index("segment")
# ======== جدول ارقام کلیدی (خلاصه‌ی مدیریتی)
kt = pd.DataFrame([("مشتریان دارای ردیف در ۱۲/۱۴۰۴", fnum(T6.customers.sum()), "نفر"), ("مانده‌ی سپرده", fnum(T6.deposit_hemat.sum(), 2), "هزار میلیارد تومان"),
                   ("مانده‌ی تسهیلات منتسب به مشتری", fnum(T6.loan_hemat.sum(), 2), "هزار میلیارد تومان"), ("مانده‌ی غیرجاری", fnum(T6.npl_hemat.sum(), 2), "هزار میلیارد تومان"),
                   ("سهم مشتریان کلان و نهادی از سپرده", fnum((T6.loc[["C1", "S"], "share_deposit"].sum()) * 100, 1), "درصد"), ("سهم سه خوشه‌ی پرریسک (C1، T و C4) از مطالبات غیرجاری", fnum(T6.loc[["C1", "T", "C4"], "share_npl"].sum() * 100, 1), "درصد")], columns=["شاخص", "مقدار", "واحد"])
kt.to_csv(TAB / "t0_1_key_figures.csv", index=False, encoding="utf-8-sig")
(TAB / "t0_1_key_figures.md").write_text("**جدول ۰-۱: ارقام کلیدی فاز دوم**\n\n| شاخص | مقدار | واحد |\n|---|---|---|\n" + "\n".join(f"| {a} | {b} | {c} |" for a, b, c in kt.values) + "\n", encoding="utf-8")

# ======== فصل 6: پویایی
cnt = pd.read_csv(D / "cluster_state_counts_by_year.csv"); ca = cnt[cnt.variant == "quantile_aligned"].pivot(index="state", columns="year", values="customers").reindex(SEG).fillna(0)
pct = ca / ca.sum() * 100; yrs = list(ca.columns)
fig, ax = plt.subplots(figsize=(9.6, 5)); bot = np.zeros(len(yrs))
for s in SEG:
    ax.bar([fd(str(y)) for y in yrs], pct.loc[s], bottom=bot, color=CLR[s], label=LAB[s], width=.62)
    for xi, (a, b) in enumerate(zip(bot, pct.loc[s])):
        if b > 4.5: ax.text(xi, a + b / 2, fnum(b, 0), ha="center", va="center", fontsize=8.5, color="white" if s in ("C1", "C2", "C4", "C7", "S", "T", "C3") else "black")
    bot += pct.loc[s].to_numpy()
ax.set_ylabel("درصد مشتریان"); ax.legend(loc="center left", bbox_to_anchor=(1.01, .5), fontsize=9); ax.grid(axis="x", visible=False); finish(fig, "f6_1_state_shares_by_year.png")

pooled = pd.read_csv(D / "s7_aligned_transition_pooled_counts.csv", index_col=0); pooled = pooled.reindex(index=SEG, columns=SEG + ["X"]).fillna(0)
pp = pooled.div(pooled.sum(1), axis=0) * 100; M = pp[SEG].values
fig, ax = plt.subplots(figsize=(9.6, 7)); im = ax.imshow(M, cmap="Blues", vmin=0, vmax=100); ax.grid(False)
ax.set_xticks(range(12)); ax.set_xticklabels(SEG); ax.set_yticks(range(12)); ax.set_yticklabels([LAB[s] for s in SEG], fontsize=9.2); ax.set_xlabel("حالت در سال بعد"); ax.xaxis.set_label_position("top"); ax.xaxis.tick_top()
for i in range(12):
    for j in range(12):
        if M[i, j] >= 1: ax.text(j, i, fnum(M[i, j], 0), ha="center", va="center", fontsize=8.3, color="white" if M[i, j] > 45 else "black")
cb = fig.colorbar(im, shrink=.7, pad=.02); cb.set_label("درصد مشتریان هر ردیف"); finish(fig, "f6_2_transition_heatmap.png")

# جدول 6-1: ماتریس گذار تجمعی
tm = pp[SEG].copy(); tm.insert(0, "حالت سال جاری", [LAB[s] for s in SEG]); tm.columns = ["حالت سال جاری"] + SEG
save_table(tm, "t6_1_transition_matrix", "جدول ۶-۱: ماتریس گذار تجمعی چهار سال (درصد مشتریان هر ردیف)", nd={s: 1 for s in SEG})

sa = pd.read_csv(D / "s7_aligned_stay_rates.csv", index_col=0).mean(axis=1) * 100; sr = pd.read_csv(D / "s7_real_stay_rates.csv", index_col=0).mean(axis=1) * 100
fig, ax = plt.subplots(figsize=(9.6, 4.4)); ss = [s for s in SEG if s != "N"]; ax.bar(ss, sa.reindex(ss), color=[CLR[s] for s in ss], width=.62)
for xi, s in enumerate(ss): ax.text(xi, sa[s] + 1.5, fnum(sa[s], 0), ha="center", fontsize=9)
ax.set_ylabel("درصد ماندن در همان حالت پس از یک سال"); ax.set_ylim(0, 108); ax.grid(axis="x", visible=False); finish(fig, "f6_3_stay_rates.png")

# مسیرهای برتر
tp = pd.read_csv(D / "s7_top_paths.csv").head(10)[::-1]
def runs(path):
    st = path.split(">"); out = [];
    for s_ in st:
        if out and out[-1][0] == s_: out[-1][1] += 1
        else: out.append([s_, 1])
    return out
def desc_path(path):
    r = runs(path)
    if len(r) == 1: return f"{r[0][0]} در هر پنج سال"
    return " سپس ".join(f"{s_} ({fd(str(n))} سال)" for s_, n in r)
fig, ax = plt.subplots(figsize=(9.2, 4.6)); ax.barh(range(len(tp)), tp.share * 100, color=NAVY, height=.6); ax.set_yticks(range(len(tp))); ax.set_yticklabels([desc_path(p) for p in tp.path], fontsize=9.5)
for yi, v in enumerate(tp.share * 100): ax.text(v + .05, yi, fnum(v, 1) + "٪", va="center", fontsize=9)
ax.set_xlabel("سهم از " + fd("467,892") + " مشتری حاضر در هر پنج سال (٪)"); ax.grid(axis="y", visible=False); ax.set_xlim(0, tp.share.max() * 100 * 1.15); finish(fig, "f6_4_top_paths.png")

db = pd.read_csv(D / "s10b_deposit_to_borrower_by_segment.csv", index_col=0); allr = 15.0
ds = [s for s in SEG if s in db.index and db.loc[s, "origin"] > 5000]
fig, ax = plt.subplots(figsize=(9.2, 4.4)); ax.bar(ds, db.loc[ds, "became_borrower"] * 100, color=[CLR[s] for s in ds], width=.62); ax.axhline(allr, color=GREY, ls="--", lw=1.2); ax.text(len(ds) - .5, allr + 1, "میانگین کل: " + fnum(allr, 0) + "٪", ha="right", fontsize=9, color=GREY)
ax.set_ylabel("درصد فقط‌سپرده‌گذاران و ضامنان که سال بعد گیرنده‌ی اصلی شدند"); ax.grid(axis="x", visible=False); finish(fig, "f6_5_deposit_to_borrower.png")

ne = pd.read_csv(D / "s7_npl_entry_by_state.csv", index_col=0); ns = [s for s in SEG if s in ne.index and ne.loc[s, "borrowers"] > 1000]
fig, ax = plt.subplots(figsize=(9.2, 4.4)); ax.bar(ns, ne.loc[ns, "npl_entry_rate"] * 100, color=[CLR[s] for s in ns], width=.62)
for xi, s in enumerate(ns): ax.text(xi, ne.loc[s, "npl_entry_rate"] * 100 + .4, fnum(ne.loc[s, "npl_entry_rate"] * 100, 1), ha="center", fontsize=9)
ax.set_ylabel("درصد وام‌گیرانی که سال بعد وارد غیرجاری شدند"); ax.grid(axis="x", visible=False); finish(fig, "f6_6_npl_entry.png")

# جدول 6-2: ماندگاری و مقصد
rows = []
for s in SEG:
    if s == "N": continue
    r_ = pp.loc[s, SEG].copy(); stay = r_[s]; r_ = r_.drop(s); top = r_.sort_values(ascending=False).iloc[:2]
    rows.append({"حالت": LAB[s], "ماندن (٪)": stay, "مقصد نخست": f"{NAME[top.index[0]]} ({top.index[0]})", "سهم مقصد نخست (٪)": top.iloc[0], "مقصد دوم": f"{NAME[top.index[1]]} ({top.index[1]})", "سهم مقصد دوم (٪)": top.iloc[1],
                 "ورود به غیرجاری در سال بعد (٪)": ne.loc[s, "npl_entry_rate"] * 100 if s in ne.index and ne.loc[s, "borrowers"] > 1000 else np.nan})
save_table(pd.DataFrame(rows), "t6_2_stay_destinations", "جدول ۶-۲: ماندگاری، مقصدهای اصلی و ورود به غیرجاری", nd={"ماندن (٪)": 1, "سهم مقصد نخست (٪)": 1, "سهم مقصد دوم (٪)": 1, "ورود به غیرجاری در سال بعد (٪)": 1})

# ======== فصل 7: جغرافیا
J = pd.read_csv(D / "s8_province_indicators.csv", index_col=0); key = lambda s: s.replace(" ", "").replace("‌", "")
J = J[~J.index.isin(["ستاد", "شعب مستقل"])]
FA = {"Tehran": "تهران", "Alborz": "البرز", "Qazvin": "قزوین", "Qom": "قم", "Markazi": "مرکزی", "Isfahan": "اصفهان", "Fars": "فارس", "Khuzestan": "خوزستان", "Kohgiluyeh and Boyer-Ahmad": "کهگیلویه و بویراحمد",
      "Bushehr": "بوشهر", "Hormozgan": "هرمزگان", "Kerman": "کرمان", "Sistan and Baluchestan": "سیستان و بلوچستان", "Yazd": "یزد", "South Khorasan": "خراسان جنوبی", "Razavi Khorasan": "خراسان رضوی",
      "North Khorasan": "خراسان شمالی", "Semnan": "سمنان", "Golestan": "گلستان", "Mazandaran": "مازندران", "Gilan": "گیلان", "Ardabil": "اردبیل", "East Azerbaijan": "آذربایجان شرقی",
      "West Azerbaijan": "آذربایجان غربی", "Zanjan": "زنجان", "Kurdistan": "کردستان", "Kermanshah": "کرمانشاه", "Ilam": "ایلام", "Lorestan": "لرستان", "Hamadan": "همدان", "Chaharmahal and Bakhtiari": "چهارمحال و بختیاری"}
Jk = J.copy(); Jk.index = [key(i) for i in Jk.index]
g = json.load(open(ROOT / "data" / "raw" / "geo" / "iran_provinces.geojson", encoding="utf-8"))
polys = lambda geom: [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
fig, axs = plt.subplots(1, 3, figsize=(15.4, 5.4)); panels = [("share_T", "سهم وام‌گیران با سپرده‌ی خدماتی (٪)", "Oranges"), ("share_C1S", "سهم مشتریان کلان و نهادی (٪)", "Blues"), ("npl_ratio", "نسبت غیرجاری در پایگاه تحلیلی (٪)", "Reds")]
for ax, (col, ttl, cmap) in zip(axs[::-1], panels):
    patches, v = [], []
    for f in g["features"]:
        nm = FA.get(f["properties"]["shapeName"]); k = key(nm) if nm else None
        if k is None or k not in Jk.index: continue
        for poly in polys(f["geometry"]): patches.append(MplPolygon(np.array(poly[0]), closed=True)); v.append(Jk.loc[k, col])
    pc = PatchCollection(patches, cmap=cmap, edgecolor="white", linewidth=.6); pc.set_array(np.array(v)); ax.add_collection(pc); ax.autoscale_view(); ax.set_aspect("equal"); ax.axis("off"); ax.set_title(ttl, fontsize=10.5)
    cb = fig.colorbar(pc, ax=ax, shrink=.65, pad=.01); cb.outline.set_visible(False)
fig.tight_layout(); finish(fig, "f7_1_province_maps.png")

pc_ = pd.read_csv(D / "s8_province_segment_pct.csv", index_col=0); pc_ = pc_[[s for s in SEG]]; pc_ = pc_[~pc_.index.isin(["ستاد", "شعب مستقل"])]
cts = pd.read_csv(D / "s8_province_segment_counts.csv", index_col=0).sum(1); order = cts.reindex(pc_.index).sort_values(ascending=False).index; Mx = pc_.loc[order].values
fig, ax = plt.subplots(figsize=(9.6, 10.2)); im = ax.imshow(Mx, cmap="Blues", aspect="auto", vmin=0, vmax=30); ax.grid(False); ax.set_xticks(range(12)); ax.set_xticklabels(SEG); ax.set_yticks(range(len(order))); ax.set_yticklabels(order, fontsize=9); ax.xaxis.tick_top()
for i in range(Mx.shape[0]):
    for j in range(12): ax.text(j, i, fnum(Mx[i, j], 0), ha="center", va="center", fontsize=7.4, color="white" if Mx[i, j] > 19 else "black")
cb = fig.colorbar(im, shrink=.55, pad=.02); cb.set_label("درصد مشتریان استان"); finish(fig, "f7_2_province_cluster_heatmap.png")

# جدول 7-1: نمایه‌ی استان‌ها
Jt = J.sort_values("deposit_hemat", ascending=False)
t71 = pd.DataFrame({"استان": Jt.index, "مشتری": Jt.customers, "سپرده (همت)": Jt.deposit_hemat, "تسهیلات (همت)": Jt.loan_hemat, "سهم وام‌گیران با سپرده‌ی خدماتی (٪)": Jt.share_T,
                    "سهم مشتریان کلان و نهادی (٪)": Jt.share_C1S, "نسبت غیرجاری نمونه (٪)": Jt.npl_ratio, "نسبت غیرجاری رسمی بانک (٪)": Jt.p1_npl_ratio})
save_table(t71, "t7_1_provinces", "جدول ۷-۱: نمایه‌ی استان‌ها بر پایه‌ی مشتریان دارای شعبه‌ی مبنا (۱۲/۱۴۰۴)", nd={"سپرده (همت)": 2, "تسهیلات (همت)": 2, "سهم وام‌گیران با سپرده‌ی خدماتی (٪)": 1, "سهم مشتریان کلان و نهادی (٪)": 1, "نسبت غیرجاری نمونه (٪)": 1, "نسبت غیرجاری رسمی بانک (٪)": 1})

# همخوانی با آمار رسمی
fig, axs = plt.subplots(1, 2, figsize=(10.8, 4.6)); sub = J.dropna(subset=["p1_npl_ratio"])
for ax, (a, b, xl, yl) in zip(axs[::-1], [("npl_ratio", "p1_npl_ratio", "نسبت غیرجاری رسمی بانک (٪)", "نسبت غیرجاری پایگاه تحلیلی (٪)"), ("ldr", "p1_ldr", "نسبت وام به سپرده‌ی رسمی بانک (٪)", "نسبت وام به سپرده‌ی پایگاه تحلیلی (٪)")]):
    from scipy.stats import spearmanr
    ax.scatter(sub[b], sub[a], color=NAVY, s=32, alpha=.85); r_ = spearmanr(sub[a], sub[b])[0]; lim = [0, max(sub[a].max(), sub[b].max()) * 1.05]; ax.plot(lim, lim, color=GREY, ls="--", lw=1)
    ax.set_xlabel(xl); ax.set_ylabel(yl); ax.set_title("همبستگی رتبه‌ای " + fnum(r_, 2), fontsize=10.5)
fig.tight_layout(); finish(fig, "f7_3_sample_vs_official.png")

bt = pd.read_csv(D / "s8_branch_concentration.csv").set_index("item"); sel = ["مشتریان", "سپرده", "تسهیلات", "غیرجاری", "مشتریان T", "مشتریان C7"]
LBL = {"مشتریان": "مشتریان", "سپرده": "مانده‌ی سپرده", "تسهیلات": "مانده‌ی تسهیلات", "غیرجاری": "مانده‌ی غیرجاری", "مشتریان T": "وام‌گیران با سپرده‌ی خدماتی", "مشتریان C7": "وام‌گیران پرریسک"}
fig, ax = plt.subplots(figsize=(9.6, 4.4)); x = np.arange(len(sel)); w = .38
ax.bar(x - w / 2, bt.loc[sel, "top10pct_branches"] * 100, w, color=NAVY, label="۱۰ درصد شعب بزرگ‌تر"); ax.bar(x + w / 2, bt.loc[sel, "top20pct_branches"] * 100, w, color=ORANGE, label="۲۰ درصد شعب بزرگ‌تر")
ax.set_xticks(x); ax.set_xticklabels([LBL[s].replace(" ", chr(10), 1) for s in sel], fontsize=9.3); ax.set_ylabel("سهم از کل (٪)"); ax.legend(ncol=2, loc="upper center", bbox_to_anchor=(.5, 1.13)); ax.grid(axis="x", visible=False)
for xi, s in enumerate(sel): ax.text(xi - w / 2, bt.loc[s, "top10pct_branches"] * 100 + 1, fnum(bt.loc[s, "top10pct_branches"] * 100, 0), ha="center", fontsize=8.6)
finish(fig, "f7_4_branch_concentration.png")

# ======== فصل 8: تعمیم
sw = pd.read_csv(D / "s9_cluster_shares_weighted.csv", index_col=0)
fig, axs = plt.subplots(1, 2, figsize=(12.4, 4.6)); x = np.arange(len(SEG)); w = .38
axs[1].bar(x - w / 2, sw.loc[SEG, "deposit_sample"], w, color=NAVY, label="پایگاه تحلیلی"); axs[1].bar(x + w / 2, sw.loc[SEG, "deposit_province"], w, color=ORANGE, label="با وزن استانی"); axs[1].set_ylabel("سهم از مانده‌ی سپرده (٪)")
axs[0].bar(x - w / 2, sw.loc[SEG, "loan_sample"], w, color=NAVY, label="پایگاه تحلیلی"); axs[0].bar(x + w / 2, sw.loc[SEG, "loan_raked"], w, color=ORANGE, label="با وزن طبقه‌ی وام و استان"); axs[0].set_ylabel("سهم از مانده‌ی تسهیلات (٪)")
for ax in axs: ax.set_xticks(x); ax.set_xticklabels(SEG, fontsize=9.5); ax.legend(loc="upper right", fontsize=9); ax.grid(axis="x", visible=False)
fig.tight_layout(); finish(fig, "f8_1_weighted_shares.png")

pw = pd.read_csv(D / "s9_province_weights.csv"); pw = pw[~pw.province.isin(["ستاد", "شعب مستقل"])].copy(); pw = pw.sort_values("official_resources", ascending=False)
t81 = pd.DataFrame({"استان": pw.province.head(10), "منابع ریالی رسمی (همت)": pw.official_resources.head(10) / 1e13, "سپرده‌ی پایگاه تحلیلی (همت)": pw.dep_s.head(10) / 1e13, "وزن سپرده": pw.w_dep.head(10),
                    "تسهیلات رسمی (همت)": pw.official_loans.head(10) / 1e13, "تسهیلات پایگاه تحلیلی (همت)": pw.loan_s.head(10) / 1e13, "وزن تسهیلات": pw.w_loan.head(10)})
save_table(t81, "t8_1_weights", "جدول ۸-۱: وزن استانی سپرده و تسهیلات در ده استان بزرگ‌تر", nd={c: 2 for c in t81.columns if c != "استان"})
pw.to_csv(TAB / "t8_1_weights_all_provinces.csv", index=False, encoding="utf-8-sig")
rg = pd.read_csv(D / "s9_share_ranges.csv", index_col=0).reindex(["C1", "C2", "C7", "C8", "T", "C4"])
t82 = pd.DataFrame({"خوشه": [LAB[s] for s in rg.index], "سهم تسهیلات: کمینه (٪)": rg["min"], "سهم تسهیلات: بیشینه (٪)": rg["max"], "سهم غیرجاری: کمینه (٪)": rg.npl_min, "سهم غیرجاری: بیشینه (٪)": rg.npl_max})
save_table(t82, "t8_2_share_ranges", "جدول ۸-۲: دامنه‌ی سهم خوشه‌ها در طرح‌های مختلف وزن‌دهی", nd={c: 1 for c in t82.columns if "٪" in c})
