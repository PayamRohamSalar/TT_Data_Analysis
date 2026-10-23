"""گزارش نهایی فاز ۲: نمودارها و جدول‌های فصل‌های 1 تا 3 (سبک نهایی؛ خروجی reports/figures/phase2_final و reports/tables_phase2)."""
from report_style import *
from sklearn.decomposition import PCA
from tt_bank.phase2_clustering.prep import Prep, NAMES, BLOCKS

mfmt = lambda v, p: (fd(f"{v / 1e6:g}") + " میلیون") if v >= 1e6 else (fd(f"{v / 1e3:g}") + " هزار") if v >= 1e3 else fd(f"{v:g}")
t61 = pd.read_csv(D / "s6_table_6_1.csv").set_index("segment"); dfn = DEFS.set_index("segment")

# ======== فصل 1
# جدول 1-1: گروه‌های تحلیلی 1404
grp = [("خوشه‌بندی اصلی (C1 تا C8)", "مشتریان گروه مدل، پس از جدا کردن وام‌گیران با سپرده‌ی خدماتی", ["C%d" % i for i in range(1, 9)]),
       ("وام‌گیران با سپرده‌ی خدماتی (T)", "گیرنده‌ی اصلی وام با گردش کمتر از سه ماه یا بیشینه‌ی مانده زیر پنج میلیون ریال", ["T"]),
       ("بی‌فعالیت (I)", "دست‌کم شش ماه حضور بدون وام، با گردش اندک یا مانده‌ی ناچیز", ["I"]),
       ("نوپا (N)", "نخستین ردیف در همان سال و سابقه‌ی کمتر از شش ماه", ["N"]),
       ("نهادی (S)", "دارای دست‌کم صد حساب در یکی از ماه‌های سال", ["S"])]
rows = []
for nm, rule, ss in grp:
    rows.append({"گروه": nm, "قاعده‌ی تعریف": rule, "تعداد مشتری": t61.loc[ss, "customers"].sum(), "سهم مشتریان (٪)": t61.loc[ss, "share_customers"].sum() * 100,
                 "سهم سپرده (٪)": t61.loc[ss, "share_deposit"].sum() * 100, "سهم تسهیلات (٪)": t61.loc[ss, "share_loan"].sum() * 100})
tot = {"گروه": "جمع", "قاعده‌ی تعریف": "همه‌ی مشتریان دارای ردیف در 1404", "تعداد مشتری": t61.customers.sum(), "سهم مشتریان (٪)": 100.0, "سهم سپرده (٪)": 100.0, "سهم تسهیلات (٪)": 100.0}
save_table(pd.DataFrame(rows + [tot]), "t1_1_groups", "جدول ۱-۱: گروه‌های تحلیلی مشتریان در ۱۲/۱۴۰۴", nd={"سهم مشتریان (٪)": 1, "سهم سپرده (٪)": 1, "سهم تسهیلات (٪)": 1})
cv = pd.read_csv(P1 / "bank_coverage_monthly.csv").set_index("year_month").loc[140412]
H = 1e13
cov = pd.DataFrame({"شاخص": ["منابع ریالی", "مانده‌ی تسهیلات", "مانده‌ی غیرجاری"], "پایگاه تحلیلی (هزار میلیارد تومان)": [cv.sample_rial_resources / H, cv.sample_loans / H, cv.sample_npl / H],
                    "کل بانک (هزار میلیارد تومان)": [cv.bank_rial_resources / H, cv.bank_loans / H, cv.bank_npl / H],
                    "پوشش (٪)": [cv.deposit_coverage_pct, cv.loan_coverage_pct, cv.npl_coverage_pct]})
save_table(cov, "t1_2_coverage", "جدول ۱-۲: پوشش پایگاه تحلیلی نسبت به کل بانک در ۱۲/۱۴۰۴", nd={"پایگاه تحلیلی (هزار میلیارد تومان)": 2, "کل بانک (هزار میلیارد تومان)": 2, "پوشش (٪)": 1})

# شکل 1-1: قیف جمعیت
c = dfn.customers_1404; cs = c[["C%d" % i for i in range(1, 9)]].sum()
steps = [("مشتریان دارای ردیف در ۱۴۰۴", c.sum()), ("پس از کنار گذاشتن گروه نهادی", c.sum() - c["S"]), ("پس از کنار گذاشتن مشتریان نوپا", c.sum() - c["S"] - c["N"]),
         ("پس از کنار گذاشتن مشتریان بی‌فعالیت", c.sum() - c["S"] - c["N"] - c["I"]), ("پس از جدا کردن وام‌گیران با سپرده‌ی خدماتی", cs)]
fig, ax = plt.subplots(figsize=(9.4, 4.2)); y = np.arange(len(steps))[::-1]
bars = ax.barh(y, [s[1] for s in steps], color=[NAVY] * 4 + [ORANGE], height=.62); ax.set_yticks(y); ax.set_yticklabels([s[0] for s in steps]); ax.grid(axis="y", visible=False)
ax.xaxis.set_major_formatter(FuncFormatter(mfmt)); ax.set_xlim(0, steps[0][1] * 1.2); ax.set_xlabel("تعداد مشتری")
for b, s in zip(bars, steps): ax.text(b.get_width() + 8000, b.get_y() + b.get_height() / 2, fnum(s[1]), va="center", fontsize=9.5)
finish(fig, "f1_1_population_funnel.png")

# شکل 1-2: رشد مشتریان در ماه
m = pd.read_csv(D / "customers_by_month.csv"); m["t"] = np.arange(len(m)); lab = [i for i in range(len(m)) if m.ym[i] % 100 == 1]; s0 = int(np.where(m.ym == 140001)[0][0])
fig, ax = plt.subplots(figsize=(9.6, 4.2)); ax.axvspan(s0, len(m) - 1, color="#EEF3F9", lw=0); ax.plot(m.t, m.customers, color=NAVY, lw=2.2, label="مشتریان دارای ردیف"); ax.plot(m.t, m.turn, color=ORANGE, lw=2.2, label="مشتریان دارای گردش")
ax.set_xticks(lab); ax.set_xticklabels([fd(f"{m.ym[i] // 100}/۰۱".replace("/۰۱", "/01")) for i in lab], fontsize=9.5); ax.yaxis.set_major_formatter(FuncFormatter(mfmt)); ax.set_ylabel("تعداد مشتری"); ax.legend(loc="upper left")
ax.text(s0 + 1, m.customers.min() * .93, "بازه‌ی تحلیل", color=NAVY, fontsize=9.5); ax.set_ylim(bottom=m.turn.min() * .85)
finish(fig, "f1_2_customers_by_month.png")

# شکل 1-3: ترکیب رابطه‌ی مشتریان
r = pd.read_csv(D / "s1_relationship_by_year.csv").set_index("y"); names = {"deposit_only": "فقط سپرده‌گذار", "party_only": "فقط ضامن یا شریک", "primary_inferred": "گیرنده‌ی اصلی (شناسایی‌شده از قرارداد)", "primary_record": "گیرنده‌ی اصلی (دارای قرارداد ثبت‌شده)"}
fig, ax = plt.subplots(figsize=(8.8, 4.4)); bot = np.zeros(len(r)); xs = [fd(str(i)) for i in r.index]
for cname, col in zip(names, [LGREY, GOLD, TEAL, NAVY]):
    v = (r[cname] / r.total * 100).to_numpy(); ax.bar(xs, v, bottom=bot, color=col, label=names[cname], width=.62)
    for xi, (a, b) in enumerate(zip(bot, v)):
        if b > 4: ax.text(xi, a + b / 2, fnum(b, 0), ha="center", va="center", fontsize=9, color="white" if col in (NAVY, TEAL) else "black")
    bot += v
ax.set_ylabel("درصد مشتریان"); ax.grid(axis="x", visible=False); ax.legend(loc="upper center", bbox_to_anchor=(.5, -.1), ncol=2, fontsize=9.5)
finish(fig, "f1_3_relationship_by_year.png")

# ======== فصل 2: طبقه‌بندی روش‌ها و جدول مقایسه
fig, ax = plt.subplots(figsize=(10.4, 5.2)); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 5.4)
box(ax, (5, 4.9), 3.2, .6, "روش‌های خوشه‌بندی مشتریان", fc=NAVY, ec=NAVY, fs=11.5, bold=True, tc="white")
fams = [("روش‌های افرازی", "K-Means\nK-Medoids", True), ("مدل‌های آمیخته", "مدل آمیخته‌ی گاوسی", True), ("سلسله‌مراتبی", "روش Ward", True),
        ("چگالی‌محور", "DBSCAN\nHDBSCAN", True), ("قاعده‌ای", "RFM\nبخش‌بندی ارزشی", True), ("ترکیبی و اجماعی", "دومرحله‌ای\nمسیر رفتاری\nاجماع", True)]
xs = np.linspace(1.15, 8.85, 6)
for x, (fam, ms, used) in zip(xs, fams):
    arrow(ax, (5, 4.58), (x, 3.78)); box(ax, (x, 3.45), 1.45, .62, fam, fc="#EAF1F8", fs=10, bold=True)
    arrow(ax, (x, 3.12), (x, 2.55)); box(ax, (x, 1.95), 1.45, 1.05 if "\n" in ms and ms.count("\n") > 1 else .85, ms, fc="white", fs=9.5)
used_by = ["روش نهایی", "مقایسه", "مقایسه", "مقایسه", "مرجع مدیریتی", "مقایسه و تکمیل"]
for x, u in zip(xs, used_by): box(ax, (x, .75), 1.45, .42, u, fc=("#FBE5D6" if u in ("روش نهایی", "مرجع مدیریتی") else "#F2F2F2"), ec=(ORANGE if u in ("روش نهایی", "مرجع مدیریتی") else LGREY), fs=9, bold=u in ("روش نهایی", "مرجع مدیریتی"))
ax.text(.05, .2, "نقش هر خانواده در این پژوهش", fontsize=9.5, color=GREY); finish(fig, "f2_1_method_taxonomy.png")

cmp = pd.DataFrame([
    ("K-Means", "افزار مشتریان به k گروه با کمینه‌کردن مجموع مجذور فاصله تا مرکز گروه", "سریع و مقیاس‌پذیر روی صدها هزار مشتری؛ مرکز هر خوشه رفتار نمونه‌ی آن را نشان می‌دهد", "به تعیین تعداد خوشه نیاز دارد و خوشه‌های کروی را ترجیح می‌دهد", "روش نهایی"),
    ("K-Medoids", "مانند K-Means ولی مرکز هر خوشه یک مشتری واقعی است", "در برابر مقادیر پرت مقاوم‌تر است", "هزینه‌ی محاسبه با مجذور تعداد مشتری رشد می‌کند و برای جمعیت چندصدهزارنفری مناسب نیست", "به‌کار نرفت"),
    ("مدل آمیخته‌ی گاوسی", "هر خوشه یک توزیع نرمال چندمتغیره؛ مشتری با احتمال به خوشه‌ها تعلق دارد", "خوشه‌های بیضوی و اندازه‌های نابرابر؛ انتخاب تعداد خوشه با معیار BIC", "به فرض نرمال و ابعاد کم حساس است", "مقایسه"),
    ("سلسله‌مراتبی (Ward)", "ادغام تدریجی نزدیک‌ترین خوشه‌ها تا ساختن درخت خوشه‌ها", "ساختار تو در تو را نشان می‌دهد و به تعداد خوشه‌ی از پیش‌تعیین‌شده نیاز ندارد", "هزینه‌ی محاسبه زیاد است؛ روی ریزخوشه‌ها اجرا می‌شود", "مقایسه"),
    ("چگالی‌محور (DBSCAN، HDBSCAN)", "خوشه یعنی ناحیه‌ی پرتراکم از مشتریان که با ناحیه‌های کم‌تراکم جدا شده است", "شکل دلخواه خوشه و شناسایی مشتریان پرت", "در داده‌های پیوسته با مرزهای نرم حساس به پارامترها است", "مقایسه"),
    ("RFM قاعده‌ای", "امتیازدهی بر پایه‌ی تازگی، تکرار و ارزش پولی و ساختن بخش‌ها با قاعده", "شفاف، مرسوم در بانکداری و زبان مشترک با مدیران", "فقط سه بُعد را می‌بیند؛ ثبات، ساختار و وام در آن نیست", "مرجع مدیریتی"),
    ("روش‌های ترکیبی و اجماعی", "ترکیب چند دید: خوشه‌بندی دومرحله‌ای، مسیر رفتاری چندساله، اجماع چند روش", "از مزیت چند روش هم‌زمان بهره می‌برد و پایداری را بالا می‌برد", "تفسیر آن‌ها پیچیده‌تر است", "مقایسه و تکمیل"),
], columns=["روش", "ایده", "مزیت", "محدودیت", "نقش در پژوهش"])
save_table(cmp, "t2_1_methods", "جدول ۲-۱: مقایسه‌ی روش‌های خوشه‌بندی مشتریان")

# ======== فصل 3
# شکل 3-1: خط لوله‌ی روش
fig, ax = plt.subplots(figsize=(10.4, 4.0)); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 4)
r1 = [("داده‌های ماهانه‌ی\nسپرده، تسهیلات و تراکنش", "#EAF1F8"), ("پانل مشتری ـ سال\nو گروه‌های قاعده‌ای", "#EAF1F8"), ("بیست‌وسه ویژگی\nدر شش بلوک", "#EAF1F8"), ("آماده‌سازی: لگاریتم،\nتعدیل تورم، استانداردسازی", "#EAF1F8")]
r2 = [("مقایسه‌ی نُه روش\nخوشه‌بندی", "#FFF2CC"), ("اعتبارسنجی: پایداری،\nاعتبار بیرونی، کاربردپذیری", "#FFF2CC"), ("مدل نهایی:\nK-Means با هشت خوشه", "#FBE5D6"), ("نمای سپرده، نمای اعتبار،\nارزش، مهاجرت، جغرافیا", "#E2EFDA")]
xr = [8.8, 6.3, 3.8, 1.3]; xl = [1.3, 3.8, 6.3, 8.8]
for x, (t, f) in zip(xr, r1): box(ax, (x, 3.1), 2.2, .95, t, fc=f, fs=9.8)
for a, b in zip(xr[:-1], xr[1:]): arrow(ax, (a - 1.1, 3.1), (b + 1.1, 3.1))
for x, (t, f) in zip(xl, r2): box(ax, (x, 1.0), 2.2, .95, t, fc=f, fs=9.8, ec=(ORANGE if "نهایی" in t else NAVY))
for a, b in zip(xl[:-1], xl[1:]): arrow(ax, (a + 1.1, 1.0), (b - 1.1, 1.0))
arrow(ax, (1.3, 2.62), (1.3, 1.48))
finish(fig, "f3_1_method_pipeline.png")

# جدول 3-1: فرهنگ ویژگی‌ها
FA = {"bal_mean_log": ("میانگین مانده‌ی سپرده", "اندازه", "میانگین مانده‌ی ماهانه‌ی کل حساب‌های سپرده در سال به ریال ثابت", "لگاریتم"),
      "bal_end_log": ("مانده‌ی پایان سال", "اندازه", "مانده‌ی سپرده در پایان سال", "لگاریتم"),
      "flow_total_log": ("گردش کل", "جریان", "مجموع گردش بستانکار و بدهکار سال", "لگاریتم"),
      "flow_ratio": ("سهم گردش بستانکار", "جریان", "نسبت گردش بستانکار به گردش کل", "نسبت"),
      "turnover_speed_log": ("سرعت گردش", "جریان", "نسبت گردش سال به میانگین مانده", "لگاریتم"),
      "net_flow_ratio": ("خالص جریان", "جریان", "اختلاف گردش بستانکار و بدهکار نسبت به گردش کل", "نسبت"),
      "ticket_cr_log": ("مبلغ تراکنش بستانکار", "جریان", "میانگین مبلغ هر تراکنش بستانکار", "لگاریتم"),
      "ticket_db_log": ("مبلغ تراکنش بدهکار", "جریان", "میانگین مبلغ هر تراکنش بدهکار", "لگاریتم"),
      "crn_log": ("تعداد تراکنش بستانکار", "فعالیت", "تعداد تراکنش‌های بستانکار سال", "لگاریتم"),
      "dbn_log": ("تعداد تراکنش بدهکار", "فعالیت", "تعداد تراکنش‌های بدهکار سال", "لگاریتم"),
      "turn_share": ("سهم ماه‌های فعال", "فعالیت", "نسبت ماه‌های دارای گردش به ماه‌های مشاهده‌شده", "نسبت"),
      "bal_cv": ("ضریب تغییرات مانده", "ثبات", "نوسان مانده‌ی ماهانه نسبت به میانگین", "خام"),
      "bal_trend": ("روند مانده", "ثبات", "شیب استاندارد مانده‌ی ماهانه در طول سال", "خام"),
      "drawdown": ("افت از بیشینه", "ثبات", "افت مانده‌ی پایان سال نسبت به بیشینه‌ی سال", "نسبت"),
      "acc_mean_log": ("تعداد حساب", "ساختار", "میانگین تعداد حساب‌های سپرده‌ی مشتری", "لگاریتم"),
      "tenure_years": ("قدمت", "ساختار", "سال‌های سپرده‌گذاری مشتری در بانک", "خام"),
      "has_loan": ("دارای وام", "وام", "وجود وام به‌عنوان گیرنده‌ی اصلی در پایان سال", "دودویی"),
      "loan_log": ("مانده‌ی وام", "وام", "مانده‌ی تسهیلات گیرنده‌ی اصلی", "لگاریتم"),
      "loan_to_dep_log": ("نسبت وام به سپرده", "وام", "مانده‌ی وام به مانده‌ی سپرده", "لگاریتم"),
      "npl_share": ("سهم غیرجاری", "وام", "نسبت مانده‌ی غیرجاری به مانده‌ی وام", "نسبت"),
      "n_loan_log": ("تعداد قرارداد", "وام", "تعداد قراردادهای وام مشتری", "لگاریتم"),
      "loan_months_y": ("سابقه‌ی وام در سال", "وام", "نسبت ماه‌های دارای وام در سال", "نسبت"),
      "guar_log": ("مانده‌ی ضمانت", "وام", "مانده‌ی تسهیلات ضمانت‌شده‌ی مشتری", "لگاریتم")}
fe = pd.DataFrame([{"بلوک": FA[n][1], "ویژگی": FA[n][0], "تعریف": FA[n][2], "تبدیل": FA[n][3]} for n in NAMES])
save_table(fe, "t3_1_features", "جدول ۳-۱: بیست‌وسه ویژگی خوشه‌بندی در شش بلوک")

# داده‌ی مدل 1404
F = pd.read_pickle(D / "features_customer_year.pkl"); pan = pd.read_pickle(D / "panel_customer_year.pkl")[["customer_id", "y", "bal_max"]]; F = F.merge(pan, on=["customer_id", "y"], how="left")
F["token"] = (F.category == "model") & F.has_primary_loan & ((F.turn_months < 3) | (F.bal_max < 5e6))
A = F[(F.y == 1404) & (F.category == "model") & ~F.token]

# شکل 3-2: اثر تبدیل لگاریتمی
fig, axs = plt.subplots(2, 3, figsize=(10.6, 5.6)); feats = [("bal_mean_r", "میانگین مانده‌ی سپرده"), ("cr_sum_r", "گردش بستانکار سال"), ("crn_sum", "تعداد تراکنش بستانکار")]
for j, (col, tt) in enumerate(feats):
    v = A[col][A[col] > 0]; hi = v.quantile(.99); axs[0, j].hist(v.clip(upper=hi), bins=60, color=GREY); axs[0, j].set_title(tt, fontsize=10.5)
    axs[1, j].hist(np.log10(v), bins=60, color=NAVY); axs[0, j].set_yticks([]); axs[1, j].set_yticks([])
    axs[0, j].set_xlabel("مقدار خام (تا صدک ۹۹)", fontsize=9.5); axs[1, j].set_xlabel("لگاریتم مبنای ۱۰", fontsize=9.5)
fig.tight_layout(h_pad=2); finish(fig, "f3_2_log_transform.png")

# شکل 3-3: همبستگی ویژگی‌ها
prep = Prep.from_json(D / "prep_spec_v2.json"); sub = A.sample(60000, random_state=20261101)
X = pd.DataFrame(prep.transform(sub, winsorize=True), columns=[FA[n][0] for n in NAMES]); C = X.corr(method="spearman")
fig, ax = plt.subplots(figsize=(9.4, 8.2)); im = ax.imshow(C.values, cmap="RdBu_r", vmin=-1, vmax=1); ax.set_xticks(range(len(C))); ax.set_xticklabels(C.columns, rotation=90, fontsize=8.5); ax.set_yticks(range(len(C))); ax.set_yticklabels(C.index, fontsize=8.5); ax.grid(False)
cb = fig.colorbar(im, shrink=.7); cb.set_label("همبستگی رتبه‌ای اسپیرمن")
finish(fig, "f3_3_feature_correlation.png")

# شکل 3-4: اثر تورم
M = F[(F.category == "model") & ~F.token]; yy = sorted(M.y.unique())
nom = [M[(M.y == y) & (M.bal_dec > 0)].bal_dec.median() for y in yy]; real = [M[(M.y == y) & (M.bal_end_r > 0)].bal_end_r.median() for y in yy]
fig, ax = plt.subplots(figsize=(8.4, 4.2)); ax.plot([fd(str(y)) for y in yy], np.array(nom) / nom[0] * 100, color=ORANGE, lw=2.4, marker="o", label="مانده‌ی اسمی")
ax.plot([fd(str(y)) for y in yy], np.array(real) / real[0] * 100, color=NAVY, lw=2.4, marker="o", label="مانده به ریال ثابت ۱۲/۱۴۰۴"); ax.set_ylabel("میانه‌ی مانده‌ی پایان سال (۱۴۰۰ = ۱۰۰)"); ax.legend()
for xx, (a, b) in enumerate(zip(np.array(nom) / nom[0] * 100, np.array(real) / real[0] * 100)):
    if xx == len(yy) - 1: ax.text(xx, a, "  " + fnum(a), va="center", fontsize=9, color=ORANGE); ax.text(xx, b, "  " + fnum(b), va="center", fontsize=9, color=NAVY)
ax.set_xlim(-.2, len(yy) - .6); finish(fig, "f3_4_inflation_effect.png")

# شکل 3-5 و جدول 3-2: مقایسه‌ی روش‌ها
MFA = {"M1": "RFM قاعده‌ای", "M2": "K-Means روی RFM گسترده", "M3": "K-Means روی همه‌ی ویژگی‌ها (وزن بلوک)", "M3n": "K-Means روی همه‌ی ویژگی‌ها (بدون وزن)", "M4": "دومرحله‌ای (رده‌ی ارزشی و K-Means)",
       "M5": "مدل آمیخته‌ی گاوسی", "M6": "Ward از ریزخوشه‌ها", "M8": "خوشه‌بندی مسیر رفتاری", "M9": "اجماع روش‌ها"}
rk = pd.read_csv(D / "s4b_method_ranking_v2.csv", encoding="utf-8-sig").sort_values("borda"); rk["fa"] = rk.method.map(MFA)
fig, ax = plt.subplots(figsize=(9.4, 4.6)); y = np.arange(len(rk))[::-1]; hi = rk.method.isin(["M3", "M2"]).to_numpy()
ax.barh(y, rk.base * 100, color=[NAVY if h else LGREY for h in hi], height=.6); ax.set_yticks(y); ax.set_yticklabels(rk.fa)
for yi, (_, rr) in zip(y, rk.iterrows()):
    sc = np.array([rr.base, rr.equal, rr.external_heavy, rr.no_internal]) * 100; ax.plot([sc.min(), sc.max()], [yi, yi], color=ORANGE, lw=2.2); ax.scatter(sc, [yi] * 4, color=ORANGE, s=14, zorder=3)
ax.set_xlabel("امتیاز کل از ۱۰۰ (میله: وزن‌دهی پایه؛ خط نارنجی: دامنه‌ی چهار وزن‌دهی)"); ax.grid(axis="y", visible=False); ax.set_xlim(0, 100)
finish(fig, "f3_5_method_scorecard.png")
bk = pd.read_csv(D / "s4_best_k_by_method.csv").set_index("method")
t32 = pd.DataFrame({"روش": rk.fa, "تعداد خوشه‌ی بهینه": [int(bk.loc[m, "k"]) for m in rk.method], "امتیاز کل (٪)": rk.base * 100, "کمترین و بیشترین امتیاز در چهار وزن‌دهی (٪)": [f"{r_.min() * 100:.0f} تا {r_.max() * 100:.0f}" for r_ in rk[["base", "equal", "external_heavy", "no_internal"]].to_numpy()], "میانگین رتبه در چهار وزن‌دهی": rk.borda.to_numpy(), "رتبه‌ی نهایی": np.arange(1, len(rk) + 1)})
save_table(t32, "t3_2_scorecard", "جدول ۳-۲: نتیجه‌ی مقایسه‌ی روش‌ها", nd={"امتیاز کل (٪)": 1, "میانگین رتبه در چهار وزن‌دهی": 2})

# شکل 3-6: انتخاب تعداد خوشه
ks = pd.read_csv(D / "s5_kselect.csv"); ks = ks[ks.method == "M3"].sort_values("k")
fig, axs = plt.subplots(2, 2, figsize=(9.6, 6.4)); spec = [("inertia", "مجموع مجذور فاصله تا مرکز (میلیون)", 1e6, ""), ("half_ari", "پایداری در نیم‌نمونه (ARI)", 1, ""), ("temporal_ari", "پایداری زمانی ۱۴۰۳ به ۱۴۰۴ (ARI)", 1, ""), ("min_share", "سهم کوچک‌ترین خوشه (٪)", .01, "")]
spec = [spec[1], spec[0], spec[3], spec[2]]
for ax, (c_, t_, sc_, un) in zip(axs.ravel(), spec):
    ax.plot(ks.k, ks[c_] / sc_, color=NAVY, lw=2.2, marker="o"); ax.scatter([8], [ks[ks.k == 8][c_].iloc[0] / sc_], s=130, color=ORANGE, zorder=4); ax.set_title(t_, fontsize=10.5); ax.set_xticks(ks.k); ax.set_xlabel("تعداد خوشه")
fig.tight_layout(h_pad=2.2); finish(fig, "f3_6_k_selection.png")

SHORT = {"M1": "RFM\nقاعده‌ای", "M2": "K-Means\nروی RFM", "M3": "K-Means\nویژگی‌ها با وزن", "M3n": "K-Means\nویژگی‌ها بدون وزن", "M4": "دومرحله‌ای", "M8": "مسیر رفتاری"}
# شکل 3-7: اعتبار بیرونی
ea = pd.read_csv(D / "s4b_external_auc.csv"); pick = [("M1", 7), ("M2", 7), ("M3", 8), ("M3n", 7), ("M4", 5), ("M8", 7)]
outs = [("auc_dormant_next", "کم‌فعال شدن در سال بعد", NAVY), ("auc_balance_halved", "نصف‌شدن مانده", TEAL), ("auc_loan_uptake", "وام‌گیری سال بعد", GOLD), ("auc_npl_entry", "ورود به غیرجاری", RED)]
fig, ax = plt.subplots(figsize=(9.8, 4.4)); x = np.arange(len(pick)); w = .2
for i, (c_, lb, col) in enumerate(outs):
    vals = [ea[(ea.method == m) & (ea.k == k)][c_].iloc[0] for m, k in pick]; ax.bar(x + (i - 1.5) * w, vals, w, color=col, label=lb)
ax.axhline(.5, color=GREY, ls="--", lw=1); ax.set_xticks(x); ax.set_xticklabels([SHORT[m] for m, _ in pick], fontsize=9.5); ax.set_ylim(.45, .9); ax.set_ylabel("سطح زیر منحنی (AUC)"); ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(.5, 1.14), fontsize=9.5); ax.grid(axis="x", visible=False)
finish(fig, "f3_7_external_validity.png")

# شکل 3-8: نمایش دوبعدی خوشه‌ها
seg = pd.read_pickle(D / "cluster_assignments_1404.pkl")[["customer_id", "segment"]]; Fm = A.merge(seg, on="customer_id"); sub = Fm.sample(40000, random_state=20261030); Xp = prep.transform(sub)
pc = PCA(2, random_state=0).fit(Xp); Z = pc.transform(Xp); ev = pc.explained_variance_ratio_
fig, ax = plt.subplots(figsize=(9.2, 6.2))
for s in ["C%d" % i for i in range(1, 9)]:
    mk = (sub.segment == s).to_numpy(); ax.scatter(Z[mk, 0], Z[mk, 1], s=3, color=CLR[s], alpha=.55, label=LAB[s])
ax.legend(markerscale=5, ncol=4, fontsize=8.6, loc="upper center", bbox_to_anchor=(.5, -.11), columnspacing=1.2); ax.set_xlabel("مؤلفه‌ی اول (" + fnum(ev[0] * 100, 0) + "٪ واریانس)"); ax.set_ylabel("مؤلفه‌ی دوم (" + fnum(ev[1] * 100, 0) + "٪ واریانس)"); ax.grid(False)
finish(fig, "f3_8_pca_clusters.png")
