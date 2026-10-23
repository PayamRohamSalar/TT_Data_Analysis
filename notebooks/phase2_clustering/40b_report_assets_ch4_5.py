"""گزارش نهایی فاز ۲: نمودارها و جدول‌های فصل‌های 4 و 5 (خوشه‌های نهایی، نمای سپرده، ارزش و ریسک، نگاه اعتباری)."""
import json
from report_style import *
from tt_bank.phase2_clustering.prep import Prep, NAMES, BLOCKS

P = pd.read_csv(D / "cluster_profiles.csv").set_index("segment"); T6 = pd.read_csv(D / "s6_table_6_1.csv").set_index("segment")
BLK = {"size": "اندازه", "flow": "جریان", "activity": "فعالیت", "stability": "ثبات", "structure": "ساختار", "loan": "وام"}
FAF = {"bal_mean_log": "میانگین مانده", "bal_end_log": "مانده‌ی پایان سال", "flow_total_log": "گردش کل", "flow_ratio": "سهم گردش بستانکار", "turnover_speed_log": "سرعت گردش", "net_flow_ratio": "خالص جریان",
       "ticket_cr_log": "مبلغ تراکنش بستانکار", "ticket_db_log": "مبلغ تراکنش بدهکار", "crn_log": "تعداد تراکنش بستانکار", "dbn_log": "تعداد تراکنش بدهکار", "turn_share": "سهم ماه‌های فعال",
       "bal_cv": "ضریب تغییرات مانده", "bal_trend": "روند مانده", "drawdown": "افت از بیشینه", "acc_mean_log": "تعداد حساب", "tenure_years": "قدمت", "has_loan": "دارای وام", "loan_log": "مانده‌ی وام",
       "loan_to_dep_log": "نسبت وام به سپرده", "npl_share": "سهم غیرجاری", "n_loan_log": "تعداد قرارداد", "loan_months_y": "سابقه‌ی وام در سال", "guar_log": "مانده‌ی ضمانت"}
MAIN = ["C%d" % i for i in range(1, 9)]


def wrap(t, n=13):
    out, cur = [], ""
    for w_ in t.split(" "):
        if cur and len(cur) + len(w_) + 1 > n: out.append(cur); cur = w_
        else: cur = (cur + " " + w_).strip()
    out.append(cur); return chr(10).join(out)


# ======== جدول 4-1: کاربرگ خوشه‌ها
desc = {}
for s in MAIN + ["T"]:
    p = P.loc[s]
    desc[s] = {
        "C1": f"قدمت میانه {fnum(p.median_tenure_years, 0)} سال، {fnum(p.share_with_loan * 100, 0)}٪ دارای وام، میانه‌ی {fnum(p.median_txn)} تراکنش در سال",
        "C2": f"{fnum(p.share_with_loan * 100, 0)}٪ وام‌گیر با مانده‌ی سپرده‌ی رو به کاهش",
        "C3": f"تنها {fnum(p.share_with_loan * 100, 0)}٪ وام‌گیر؛ مانده‌ی سپرده‌ی رو به افزایش",
        "C4": f"میانه‌ی {fnum(p.median_txn)} تراکنش در سال و مانده‌ی بسیار باثبات؛ اقلیت وام‌دار با نسبت غیرجاری بالا",
        "C5": f"میانه‌ی {fnum(p.median_txn)} تراکنش در سال با مانده‌ی کوچک؛ تقریباً بدون وام",
        "C6": f"گردش در {fnum(p.mean_turn_share * 100, 0)}٪ ماه‌ها؛ مانده‌ی کوچک",
        "C7": f"{fnum(p.share_with_loan * 100, 0)}٪ وام‌گیر با سپرده‌ی ناچیز و مانده‌ی رو به کاهش",
        "C8": f"{fnum(p.share_with_loan * 100, 0)}٪ وام‌گیر با نسبت غیرجاری {fnum(T6.loc['C8', 'npl_ratio'] * 100, 1)}٪",
        "T": f"{fnum(p.share_with_loan * 100, 0)}٪ وام‌گیر با سپرده‌ی ناچیز و میانه‌ی {fnum(p.median_txn)} تراکنش در سال"}[s]
rows = []
for s in MAIN + ["T"]:
    p = P.loc[s]; rows.append({"خوشه": f"{NAME[s]} ({s})", "تعداد مشتری": p.customers, "سهم مشتریان (٪)": p.share_customers * 100, "سهم سپرده (٪)": p.share_deposit * 100, "سهم تسهیلات (٪)": p.share_loan * 100,
                              "میانه‌ی مانده‌ی میانگین (میلیون تومان)": p.median_bal_mean_mtoman, "ویژگی بارز": desc[s]})
save_table(pd.DataFrame(rows), "t4_1_cluster_sheet", "جدول ۴-۱: کاربرگ خوشه‌های نهایی در ۱۲/۱۴۰۴", nd={"سهم مشتریان (٪)": 1, "سهم سپرده (٪)": 1, "سهم تسهیلات (٪)": 1, "میانه‌ی مانده‌ی میانگین (میلیون تومان)": 2})

# ======== شکل 4-1: سهم تعدادی و مبلغی
fig, ax = plt.subplots(figsize=(10.4, 4.8)); x = np.arange(len(SEG)); w = .26
for k, (c, col, lb) in enumerate([("share_customers", NAVY, "سهم مشتریان"), ("share_deposit", ORANGE, "سهم سپرده"), ("share_loan", GREEN, "سهم تسهیلات")]):
    ax.bar(x + (k - 1) * w, T6[c].reindex(SEG) * 100, w, color=col, label=lb)
ax.set_xticks(x); ax.set_xticklabels(SEG); ax.set_ylabel("درصد از کل"); ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(.5, 1.13)); ax.grid(axis="x", visible=False)
finish(fig, "f4_1_cluster_shares.png")

# ======== شکل 4-2: نقشه‌ی گرمایی مراکز
prep = Prep.from_json(D / "prep_spec_v2.json"); cen = np.array(json.load(open(D / "s5_final_centers.json"))["centers_std"]); z = cen / np.array([prep.weight[n] for n in NAMES])[None, :]
order = list(range(len(NAMES))); Z = pd.DataFrame(z.T, index=[FAF[n] for n in NAMES], columns=MAIN)
fig, ax = plt.subplots(figsize=(8.6, 8.2)); im = ax.imshow(Z.values, cmap="RdBu_r", vmin=-2.5, vmax=2.5, aspect="auto"); ax.grid(False)
ax.set_xticks(range(8)); ax.set_xticklabels([wrap(NAME[s]) + chr(10) + "(" + s + ")" for s in MAIN], fontsize=8.4); ax.set_yticks(range(len(Z))); ax.set_yticklabels(Z.index, fontsize=9); ax.xaxis.tick_top()
for i in range(Z.shape[0]):
    for j in range(8): ax.text(j, i, fd(f"{Z.values[i, j]:.1f}"), ha="center", va="center", fontsize=7.6, color="white" if abs(Z.values[i, j]) > 1.6 else "black")
bl = [BLK[b] for b in BLOCKS]
for i in range(1, len(bl)):
    if bl[i] != bl[i - 1]: ax.axhline(i - .5, color="white", lw=2.5)
cb = fig.colorbar(im, shrink=.6, pad=.02); cb.set_label("میانگین استاندارد ویژگی در خوشه")
finish(fig, "f4_2_cluster_heatmap.png")

# ======== شکل 4-3: رادار بلوک‌ها
blocks = list(BLK); zb = pd.DataFrame({b: z[:, [i for i, bb in enumerate(BLOCKS) if bb == b]].mean(axis=1) for b in blocks}, index=MAIN)
ang = np.linspace(0, 2 * np.pi, len(blocks), endpoint=False)[::-1]; ang = np.r_[ang, ang[0]]
fig, axs = plt.subplots(2, 4, figsize=(11.4, 6.2), subplot_kw=dict(polar=True))
for ax, s in zip(axs.ravel(), MAIN):
    v = np.r_[zb.loc[s].values, zb.loc[s].values[0]]; ax.plot(ang, v, color=CLR[s], lw=2); ax.fill(ang, v, color=CLR[s], alpha=.25); ax.set_ylim(-1.6, 1.6); ax.set_yticks([-1, 0, 1]); ax.set_yticklabels([])
    ax.set_xticks(ang[:-1]); ax.set_xticklabels([BLK[b] for b in blocks], fontsize=8.5); ax.set_title(f"{NAME[s]} ({s})", fontsize=10, pad=14); ax.grid(True, color="#E0E0E0")
fig.tight_layout(h_pad=2.4); finish(fig, "f4_3_cluster_radar.png")

# ======== شکل 4-4: توزیع مانده‌ی سپرده
F = pd.read_pickle(D / "features_customer_year.pkl"); G = F[F.y == 1404].merge(pd.read_pickle(D / "cluster_assignments_1404.pkl")[["customer_id", "segment"]], on="customer_id"); G["segment"] = G.segment.replace({"O": "I"})
vals = [np.log10(G[(G.segment == s) & (G.bal_mean_r > 0)].bal_mean_r / 1e7) for s in MAIN + ["T"]]
fig, ax = plt.subplots(figsize=(9.6, 4.8)); bp = ax.boxplot(vals, vert=True, patch_artist=True, showfliers=False, widths=.55, medianprops=dict(color="white", lw=2))
for b, s in zip(bp["boxes"], MAIN + ["T"]): b.set(facecolor=CLR[s], edgecolor=CLR[s])
for k in ("whiskers", "caps"): [l.set(color=GREY) for l in bp[k]]
ax.set_xticks(range(1, 10)); ax.set_xticklabels(MAIN + ["T"]); ticks = [-2, -1, 0, 1, 2, 3, 4]; ax.set_yticks(ticks); ax.set_yticklabels([fd(f"{10 ** t:g}") for t in ticks]); ax.set_ylabel("میانگین مانده‌ی سپرده (میلیون تومان، مقیاس لگاریتمی)"); ax.grid(axis="x", visible=False)
finish(fig, "f4_4_balance_distribution.png")

# ======== شکل 4-5: ترکیب نوع سپرده
tp = [("share_type_long", "سرمایه‌گذاری بلندمدت", NAVY), ("share_type_short", "سرمایه‌گذاری کوتاه‌مدت", TEAL), ("share_type_qard", "قرض‌الحسنه پس‌انداز", GREEN), ("share_type_current", "جاری", GOLD), ("share_type_special", "ویژه", PURPLE), ("mean_unknown_type", "نوع ثبت‌نشده", LGREY)]
bs = MAIN + ["S"]; M = np.array([[P.loc[s, c] for c, _, _ in tp] for s in bs]); M = M / M.sum(1, keepdims=True) * 100
fig, ax = plt.subplots(figsize=(9.8, 4.8)); bot = np.zeros(len(bs))
for j, (_, lb, col) in enumerate(tp): ax.bar(bs, M[:, j], bottom=bot, color=col, label=lb, width=.62); bot += M[:, j]
ax.set_ylabel("درصد مانده‌ی سپرده"); ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(.5, -.07), fontsize=9.5); ax.grid(axis="x", visible=False); finish(fig, "f4_5_account_type_mix.png")

# ======== نمای سپرده (لنز سپرده)
dl = pd.read_csv(D / "s5b_deposit_lens_profile.csv"); DLN = {1: "سپرده‌گذاران بزرگ و فعال", 2: "میان‌رده‌ی رو به کاهش", 3: "خرد رو به رشد", 4: "حساب‌های ایستا", 5: "حساب‌های تقریباً خالی"}
t42 = pd.DataFrame({"گروه": [DLN[i] for i in dl.lens], "تعداد مشتری": dl.customers, "سهم مشتریان (٪)": dl.share_customers * 100, "سهم سپرده (٪)": dl.deposit_share * 100, "سهم تسهیلات (٪)": dl.loan_share * 100,
                    "میانه‌ی مانده (میلیون تومان)": dl.median_balance_mtoman, "میانه‌ی تراکنش سالانه": dl.median_txn, "روند مانده": dl.mean_trend, "دارای وام (٪)": dl.share_with_loan * 100})
save_table(t42, "t4_2_deposit_view", "جدول ۴-۲: نمای سپرده‌ای، پنج گروه مشتریان بر پایه‌ی رفتار سپرده", nd={"سهم مشتریان (٪)": 1, "سهم سپرده (٪)": 1, "سهم تسهیلات (٪)": 1, "میانه‌ی مانده (میلیون تومان)": 1, "روند مانده": 2, "دارای وام (٪)": 0})
fig, ax = plt.subplots(figsize=(9.4, 4.4)); x = np.arange(len(dl)); w = .27
for k, (c, col, lb) in enumerate([("share_customers", NAVY, "سهم مشتریان"), ("deposit_share", ORANGE, "سهم سپرده"), ("loan_share", GREEN, "سهم تسهیلات")]): ax.bar(x + (k - 1) * w, dl[c] * 100, w, color=col, label=lb)
ax.set_xticks(x); ax.set_xticklabels([DLN[i].replace(" ", "\n", 1) if len(DLN[i]) > 14 else DLN[i] for i in dl.lens], fontsize=9); ax.set_ylabel("درصد از کل"); ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(.5, 1.13)); ax.grid(axis="x", visible=False)
finish(fig, "f4_6_deposit_view.png")
ct = pd.read_csv(D / "s5b_deposit_lens_crosstab.csv", index_col=0); ct = ct[[s for s in SEG if s in ct.columns]]; pc = ct.div(ct.sum(1), axis=0) * 100
fig, ax = plt.subplots(figsize=(9.6, 4.2)); im = ax.imshow(pc.values, cmap="Blues", aspect="auto", vmin=0, vmax=60); ax.grid(False)
ax.set_xticks(range(pc.shape[1])); ax.set_xticklabels(pc.columns); ax.set_yticks(range(5)); ax.set_yticklabels([DLN[i] for i in pc.index], fontsize=9.5); ax.set_xlabel("خوشه‌ی اصلی")
for i in range(pc.shape[0]):
    for j in range(pc.shape[1]): ax.text(j, i, fnum(pc.values[i, j], 0), ha="center", va="center", fontsize=8.5, color="white" if pc.values[i, j] > 35 else "black")
cb = fig.colorbar(im, shrink=.8); cb.set_label("درصد مشتریان گروه")
finish(fig, "f4_7_deposit_view_crosstab.png")

# ======== فصل 5
r = []
for s in SEG:
    t = T6.loc[s]; r.append({"خوشه": f"{NAME[s]} ({s})", "مشتری": t.customers, "سهم مشتریان (٪)": t.share_customers * 100, "سپرده (همت)": t.deposit_hemat, "سهم سپرده (٪)": t.share_deposit * 100,
                             "تسهیلات (همت)": t.loan_hemat, "سهم تسهیلات (٪)": t.share_loan * 100, "غیرجاری (همت)": t.npl_hemat, "سهم غیرجاری (٪)": t.share_npl * 100, "نسبت غیرجاری (٪)": t.npl_ratio * 100})
tt = pd.DataFrame(r); tot = {"خوشه": "جمع", "مشتری": T6.customers.sum(), "سهم مشتریان (٪)": 100.0, "سپرده (همت)": T6.deposit_hemat.sum(), "سهم سپرده (٪)": 100.0, "تسهیلات (همت)": T6.loan_hemat.sum(), "سهم تسهیلات (٪)": 100.0,
                           "غیرجاری (همت)": T6.npl_hemat.sum(), "سهم غیرجاری (٪)": 100.0, "نسبت غیرجاری (٪)": T6.npl_hemat.sum() / T6.loan_hemat.sum() * 100}
save_table(pd.concat([tt, pd.DataFrame([tot])], ignore_index=True), "t5_1_value_risk", "جدول ۵-۱: سهم خوشه‌ها از مشتریان، سپرده، تسهیلات و مطالبات غیرجاری در ۱۲/۱۴۰۴",
           nd={"سهم مشتریان (٪)": 1, "سپرده (همت)": 2, "سهم سپرده (٪)": 1, "تسهیلات (همت)": 2, "سهم تسهیلات (٪)": 1, "غیرجاری (همت)": 2, "سهم غیرجاری (٪)": 1, "نسبت غیرجاری (٪)": 1})

# شکل 5-1: سهم تعدادی و مبلغی (مشتری، سپرده، تسهیلات، غیرجاری)
fig, ax = plt.subplots(figsize=(10.6, 4.8)); x = np.arange(len(SEG)); w = .2
for k, (c, col, lb) in enumerate([("share_customers", NAVY, "مشتریان"), ("share_deposit", ORANGE, "سپرده"), ("share_loan", GREEN, "تسهیلات"), ("share_npl", RED, "مطالبات غیرجاری")]): ax.bar(x + (k - 1.5) * w, T6[c].reindex(SEG) * 100, w, color=col, label=lb)
ax.set_xticks(x); ax.set_xticklabels(SEG); ax.set_ylabel("سهم از کل (٪)"); ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(.5, 1.13)); ax.grid(axis="x", visible=False); finish(fig, "f5_1_count_vs_amount.png")

# شکل 5-2: منحنی تمرکز
G["dep"] = G.bal_dec.fillna(0); G["loan"] = G.loan_dec_r.fillna(0); G["npl"] = G.npl_dec_r.fillna(0)
def conc(v):
    v = np.sort(v.to_numpy())[::-1]; return np.cumsum(v) / v.sum()
cd, cl, cn = conc(G.dep), conc(G.loan), conc(G.npl); n = len(G); xs = np.arange(1, n + 1) / n * 100; idx = np.unique(np.r_[np.arange(0, 3000, 5), np.arange(3000, n, 400), n - 1])
fig, ax = plt.subplots(figsize=(8.4, 5.2)); ax.plot(xs[idx], cd[idx] * 100, color=NAVY, lw=2.4, label="مانده‌ی سپرده"); ax.plot(xs[idx], cl[idx] * 100, color=GREEN, lw=2.4, label="مانده‌ی تسهیلات"); ax.plot(xs[idx], cn[idx] * 100, color=RED, lw=2.4, label="مانده‌ی غیرجاری")
ax.set_xscale("log"); ax.set_xlim(.01, 100); ax.set_ylim(0, 101); ax.set_xticks([.01, .1, 1, 10, 100]); ax.set_xticklabels([fd(t) for t in ["0.01", "0.1", "1", "10", "100"]]); ax.set_xlabel("درصد مشتریان از بزرگ‌ترین مانده (مقیاس لگاریتمی)"); ax.set_ylabel("سهم تجمعی از کل (٪)"); ax.legend(loc="lower right")
for f_, yv in [(1, cd), (1, cl), (1, cn)]: ax.scatter([1], [yv[int(n * .01) - 1] * 100], color="black", s=18, zorder=5)
ax.set_ylim(0, 103); ax.set_yticks([0, 20, 40, 60, 80, 100]); finish(fig, "f5_2_concentration_curve.png")
pd.DataFrame({"top_fraction": [.001, .01, .05, .10], "deposit": [cd[int(n * f) - 1] for f in (.001, .01, .05, .10)], "loan": [cl[int(n * f) - 1] for f in (.001, .01, .05, .10)], "npl": [cn[int(n * f) - 1] for f in (.001, .01, .05, .10)]}).to_csv(TAB / "t5_x_concentration.csv", index=False)

# شکل 5-3: نسبت و سهم غیرجاری
fig, axs = plt.subplots(1, 2, figsize=(11.4, 4.4)); bsel = [s for s in SEG if s != "I"]
axs[0].bar(bsel, T6.npl_ratio.reindex(bsel) * 100, color=[CLR[s] for s in bsel], width=.62); axs[0].set_ylabel("نسبت غیرجاری به تسهیلات (٪)"); axs[0].grid(axis="x", visible=False)
axs[1].bar(bsel, T6.share_npl.reindex(bsel) * 100, color=[CLR[s] for s in bsel], width=.62); axs[1].set_ylabel("سهم از کل مانده‌ی غیرجاری (٪)"); axs[1].grid(axis="x", visible=False)
for ax, col in zip(axs, ["npl_ratio", "share_npl"]):
    for xi, s in enumerate(bsel): ax.text(xi, T6.loc[s, col] * 100 + 1, fnum(T6.loc[s, col] * 100, 0), ha="center", fontsize=8.5)
finish(fig, "f5_3_npl_by_cluster.png")

# شکل 5-4: حباب
fig, ax = plt.subplots(figsize=(8.8, 6)); pp = T6.loc[[s for s in SEG if s != "I"]]
sc = ax.scatter(pp.deposit_hemat, pp.loan_hemat, s=70 + pp.customers / 250, c=pp.npl_ratio * 100, cmap="Reds", edgecolor=GREY, vmin=0, vmax=60, alpha=.9)
for s, rr in pp.iterrows(): ax.annotate(s, (rr.deposit_hemat, rr.loan_hemat), ha="center", va="center", fontsize=9)
ax.set_ylim(-3, 74); ax.set_xscale("symlog", linthresh=1); ax.set_xlim(-.05, 120); ax.set_xticks([0, 1, 10, 50]); ax.set_xticklabels([fd(t) for t in ["0", "1", "10", "50"]]); ax.set_xlabel("مانده‌ی سپرده (همت، مقیاس لگاریتمی)"); ax.set_ylabel("مانده‌ی تسهیلات (همت)")
cb = fig.colorbar(sc); cb.set_label("نسبت غیرجاری (٪)"); ax.text(.02, .97, "اندازه‌ی دایره: تعداد مشتری", transform=ax.transAxes, fontsize=9, color=GREY, va="top")
finish(fig, "f5_4_bubble.png")

# شکل 5-5: رفتار پرداخت اقساط (نسبی)
bs = [s for s in SEG if T6.loc[s, "borrowers"] > 1000 and s != "I"]
fig, ax = plt.subplots(figsize=(9.6, 4.4)); x = np.arange(len(bs)); w = .38
ax.bar(x - w / 2, T6.loc[bs, "late30"] * 100, w, color=ORANGE, label="اقساط با تأخیر پرداخت بیش از ۳۰ روز"); ax.bar(x + w / 2, T6.loc[bs, "late90"] * 100, w, color=RED, label="اقساط با تأخیر پرداخت بیش از ۹۰ روز")
ax.set_xticks(x); ax.set_xticklabels(bs); ax.set_ylabel("سهم از اقساط (٪)"); ax.legend(ncol=2, loc="upper center", bbox_to_anchor=(.5, 1.13)); ax.grid(axis="x", visible=False); finish(fig, "f5_5_late_payment.png")

# شکل 5-6: شاخص نسبی هزینه‌ی سود
ib = [s for s in SEG if T6.loc[s, "interest_coverage"] > 0 and s not in ("N", "I")]; base = T6.loc["C1", "interest_per_deposit"]
fig, ax = plt.subplots(figsize=(9.2, 4.2)); v = T6.loc[ib, "interest_per_deposit"] / base * 100; ax.bar(ib, v, color=[CLR[s] for s in ib], width=.62); ax.axhline(100, color=GREY, ls="--", lw=1)
for xi, vv in enumerate(v): ax.text(xi, vv + 2, fnum(vv, 0), ha="center", fontsize=9)
ax.set_ylabel("نسبت سود پرداختی به مانده (شاخص نسبی، C1 = ۱۰۰)"); ax.grid(axis="x", visible=False); finish(fig, "f5_6_interest_index.png")

# شکل 5-7: ترکیب نوع وام
bs = ["C1", "C2", "C3", "C6", "C7", "C8", "T", "N"]   # خوشه‌هایی با بیش از ۲٬۰۰۰ وام‌گیر
q, mu, ins = P.loc[bs, "share_ltype_qard"], P.loc[bs, "share_ltype_murabaha"], P.loc[bs, "share_ltype_installment"]; oth = (1 - q - mu - ins).clip(lower=0)
fig, ax = plt.subplots(figsize=(9.6, 4.6)); bot = np.zeros(len(bs))
for v_, col, lb in [(mu, NAVY, "مرابحه"), (q, GREEN, "قرض‌الحسنه"), (ins, ORANGE, "اقساطی"), (oth, LGREY, "سایر")]: ax.bar(bs, v_.to_numpy() * 100, bottom=bot, color=col, label=lb, width=.62); bot += v_.to_numpy() * 100
ax.set_ylabel("درصد مانده‌ی وام"); ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(.5, 1.13)); ax.grid(axis="x", visible=False); finish(fig, "f5_7_loan_type_mix.png")

# نگاه اعتباری (لنز اعتبار)
cl_ = pd.read_csv(D / "s5b_credit_lens_v2_profile.csv"); CLN = {1: "وام‌گیران بخش مسکن", 2: "بدهکار با سپرده‌ی تهی", 3: "مرابحه‌ی پرنرخ بخش خدمات", 4: "وام‌گیران قرض‌الحسنه"}
t52 = pd.DataFrame({"گروه": [CLN[i] for i in cl_.lens], "وام‌گیر": cl_.borrowers, "سهم وام‌گیران (٪)": cl_.share_borrowers * 100, "سهم تسهیلات (٪)": cl_.loan_share * 100, "نسبت غیرجاری (٪)": cl_.npl_ratio * 100,
                    "سهم از غیرجاری (٪)": cl_.npl_share_of_total * 100, "اقساط با تأخیر بیش از ۳۰ روز (٪)": cl_.late30 * 100, "نرخ سود (٪)": cl_.rate, "از گروه T (٪)": cl_.share_token * 100})
save_table(t52, "t5_2_credit_view", "جدول ۵-۲: نگاه اعتباری، چهار گروه گیرندگان اصلی تسهیلات", nd={c: 1 for c in t52.columns if "٪" in c})
fig, ax = plt.subplots(figsize=(9.4, 4.4)); x = np.arange(len(cl_)); w = .27
for k, (c, col, lb) in enumerate([("share_borrowers", NAVY, "سهم وام‌گیران"), ("loan_share", GREEN, "سهم تسهیلات"), ("npl_share_of_total", RED, "سهم مطالبات غیرجاری")]): ax.bar(x + (k - 1) * w, cl_[c] * 100, w, color=col, label=lb)
ax.set_xticks(x); ax.set_xticklabels([CLN[i].replace(" ", "\n", 1) for i in cl_.lens], fontsize=9.5); ax.set_ylabel("درصد از کل"); ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(.5, 1.13)); ax.grid(axis="x", visible=False)
finish(fig, "f5_8_credit_view.png")

# پتانسیل ناخالص فروش تسهیلات
t2 = pd.read_csv(D / "s6_table_6_2.csv"); t2 = t2[t2.segment.isin(["C1", "C3", "C6"])]
t53 = pd.DataFrame({"خوشه": [f"{NAME[s]} ({s})" for s in t2.segment], "سپرده‌گذار بدون وام": t2.no_loan_customers, "دارای مانده‌ی کافی": t2.eligible, "سپرده‌ی دارای مانده‌ی کافی (همت)": t2.eligible_deposit_hemat,
                    "با مانده‌ی ۱۰۰ میلیون تومان و بیشتر": t2.eligible_100mt, "سپرده‌ی گروه ۱۰۰ میلیون تومان و بیشتر (همت)": t2.eligible_100mt_deposit_hemat, "میانه‌ی وام وام‌گیران خوشه (میلیون تومان)": t2.borrower_median_loan_mtoman, "سقف محاسباتی (همت)": t2.reference_ceiling_hemat})
save_table(t53, "t5_3_sales_potential", "جدول ۵-۳: پتانسیل ناخالص فروش تسهیلات به سپرده‌گذاران بدون وام", nd={"سپرده‌ی دارای مانده‌ی کافی (همت)": 2, "سپرده‌ی گروه ۱۰۰ میلیون تومان و بیشتر (همت)": 2, "میانه‌ی وام وام‌گیران خوشه (میلیون تومان)": 0, "سقف محاسباتی (همت)": 2})
fig, ax = plt.subplots(figsize=(8.4, 4.2)); x = np.arange(len(t2)); w = .38
ax.bar(x - w / 2, t2.eligible_100mt, w, color=NAVY, label="تعداد مشتری با مانده‌ی ۱۰۰ میلیون تومان و بیشتر"); ax.set_ylabel("تعداد مشتری"); ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p: fd(f"{v / 1e3:g}") + " هزار")); ax2 = ax.twinx()
ax2.bar(x + w / 2, t2.eligible_100mt_deposit_hemat, w, color=ORANGE, label="سپرده‌ی آنان (همت)"); ax2.set_ylabel("سپرده (همت)"); ax2.grid(False); ax2.spines["right"].set_visible(True)
ax.set_xticks(x); ax.set_xticklabels(t2.segment); ax.grid(axis="x", visible=False); h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels(); ax.legend(h1 + h2, l1 + l2, loc="upper right", fontsize=9)
finish(fig, "f5_9_sales_potential.png")
