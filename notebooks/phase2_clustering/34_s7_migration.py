"""فاز ۲ - S7: مهاجرت مشتریان بین خوشه‌ها 1400 تا 1404 با مراکز ثابت مدل 1404 (بدون DB).
دو نسخه: (الف) هم‌ترازی چندکی هر سال به توزیع 1404 (پیش‌فرض D14)، (ب) ریال ثابت 12/1404 با CPI و بدون هم‌ترازی (حساسیت).
حالت‌ها: C1..C8 (نزدیک‌ترین مرکز)، T، I (بی‌فعالیت یا نمادین)، N (نوپا)، S (نهادی)، X (غایب در آن سال).
خروجی: s7_*.csv و reports/figures/phase2_clustering/ch7_*.png"""
import json
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter, ScalarFormatter
from sklearn.metrics import adjusted_rand_score
from tt_bank.common.persian_plot import FONTS_DIR, setup_persian_font, to_persian_digits
from tt_bank.phase2_clustering.prep import Prep

ROOT = Path(__file__).resolve().parents[2]; D = ROOT / "data" / "processed" / "phase2_clustering"; FIG = ROOT / "reports" / "figures" / "phase2_clustering"
setup_persian_font(); font_manager.fontManager.addfont(str(FONTS_DIR / "Vazirmatn-Bold.ttf"))
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 11, "savefig.dpi": 200, "axes.grid": False, "axes.axisbelow": True})
fd = to_persian_digits; BLUE, ORANGE, GREEN, RED, GREY = "#1F4E79", "#C55A11", "#548235", "#B03A2E", "#7F7F7F"
def save(fig, name):
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            if isinstance(axis.get_major_formatter(), ScalarFormatter): axis.set_major_formatter(FuncFormatter(lambda v, pos: fd(f"{v:g}")))
    fig.savefig(FIG / name, bbox_inches="tight", facecolor="white"); plt.close(fig); print("saved", name)

YEARS = [1400, 1401, 1402, 1403, 1404]; STATES = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "T", "I", "N", "S", "X"]
F = pd.read_pickle(D / "features_customer_year.pkl")
pan = pd.read_pickle(D / "panel_customer_year.pkl")[["customer_id", "y", "bal_max"]]; F = F.merge(pan, on=["customer_id", "y"], how="left")
F["token_borrower"] = (F.category == "model") & F.has_primary_loan & ((F.turn_months < 3) | (F.bal_max < 5e6))
prep = Prep.from_json(D / "prep_spec_v2.json"); C = np.array(json.load(open(D / "s5_final_centers.json"))["centers_std"], dtype="float32")
print("تعداد ردیف:", len(F), " مراکز:", C.shape)

def assign(df, aligned):
    X = prep.transform(df, aligned=aligned).astype("float32")
    d = (X ** 2).sum(1)[:, None] - 2 * X @ C.T + (C ** 2).sum(1)[None, :]
    return d.argmin(1) + 1

def states(aligned):
    out = {}
    for y in YEARS:
        g = F[F.y == y].reset_index(drop=True); st = pd.Series("O", index=g.index)
        st[g.category == "institutional_candidate"] = "S"; st[g.category == "newcomer"] = "N"; st[g.category == "idle_token"] = "I"; st[g.token_borrower] = "T"
        m = ((g.category == "model") & ~g.token_borrower).to_numpy(); lab = assign(g[m], aligned)
        st[m] = ["C%d" % k for k in lab]
        st[st == "O"] = "I"
        out[y] = pd.Series(st.to_numpy(), index=g.customer_id.to_numpy())
    return out

# بررسی: بازتولید برچسب‌های نهایی 1404
SA = states(True); SR = states(False)
ref = pd.read_pickle(D / "cluster_assignments_1404.pkl").set_index("customer_id").segment.replace({"O": "I"})
chk = (SA[1404].reindex(ref.index) == ref).mean(); print("بازتولید تخصیص 1404 از نزدیک‌ترین مرکز: %.5f" % chk); assert chk > 0.999
chk2 = (SR[1404].reindex(ref.index) == ref).mean(); print("نسخه‌ی ریال ثابت 1404 (باید برابر): %.5f" % chk2)

def share_table(S):
    return pd.DataFrame({y: S[y].value_counts().reindex(STATES[:-1]).fillna(0).astype(int) for y in YEARS})
def transitions(S):
    tot = {}; allc = None
    for y in YEARS[:-1]:
        a, b = S[y], S[y + 1]; idx = a.index
        d = b.reindex(idx).fillna("X"); ct = pd.crosstab(a, d).reindex(index=STATES[:-1], columns=STATES).fillna(0).astype(int)
        tot[y] = ct; allc = ct if allc is None else allc + ct
    return tot, allc
def rowpct(ct): return ct.div(ct.sum(1).replace(0, np.nan), axis=0) * 100

res = {}
for name, S in (("aligned", SA), ("real", SR)):
    sh = share_table(S); sh.to_csv(D / f"s7_{name}_counts_by_year.csv")
    tr, pooled = transitions(S)
    for y, ct in tr.items(): ct.to_csv(D / f"s7_{name}_transition_{y}_{y+1}_counts.csv"); rowpct(ct).round(2).to_csv(D / f"s7_{name}_transition_{y}_{y+1}_pct.csv")
    pooled.to_csv(D / f"s7_{name}_transition_pooled_counts.csv"); rowpct(pooled).round(2).to_csv(D / f"s7_{name}_transition_pooled_pct.csv")
    # ورودی‌ها (غایب در سال قبل → حاضر)
    ent = []
    for y in YEARS[1:]:
        e = S[y][~S[y].index.isin(S[y - 1].index)]; ent.append(dict(year=y, entrants=len(e), **e.value_counts().reindex(STATES[:-1]).fillna(0).astype(int).to_dict()))
    pd.DataFrame(ent).to_csv(D / f"s7_{name}_entrants.csv", index=False)
    stay = {s: [tr[y].loc[s, s] / tr[y].loc[s].sum() if tr[y].loc[s].sum() > 0 else np.nan for y in tr] for s in STATES[:-1]}
    pd.DataFrame(stay, index=[f"{y}->{y+1}" for y in tr]).T.to_csv(D / f"s7_{name}_stay_rates.csv")
    res[name] = dict(sh=sh, tr=tr, pooled=pooled, ent=pd.DataFrame(ent))
    print("\n==", name, "\nشمار هر حالت در سال:\n", sh.to_string(), "\nماتریس تجمعی (درصد سطری):\n", rowpct(pooled).round(1).to_string(), "\nورودی‌ها:\n", pd.DataFrame(ent).to_string())

# توافق دو نسخه در هر سال (مشتریان گروه C)
agree = []
for y in YEARS:
    a, b = SA[y], SR[y]; m = a.str.startswith("C") & b.str.startswith("C")
    agree.append(dict(year=y, n_C=int(m.sum()), same_label=float((a[m] == b[m]).mean()), ari=adjusted_rand_score(a[m], b[m]), share_C_aligned=float(a.str.startswith("C").mean()), share_C_real_any=float(b.str.startswith("C").mean())))
A_ = pd.DataFrame(agree); A_.to_csv(D / "s7_aligned_vs_real_agreement.csv", index=False); print("\nتوافق نسخه‌ی هم‌ترازی و ریال ثابت:\n", A_.round(3).to_string())

# مسیرها: مشتریان حاضر در هر پنج سال
common = SA[1400].index
for y in YEARS[1:]: common = common.intersection(SA[y].index)
P = pd.DataFrame({y: SA[y].reindex(common) for y in YEARS}); P["path"] = P[YEARS].agg(">".join, axis=1)
tp = P.path.value_counts().head(25).rename_axis("path").reset_index(name="customers"); tp["share"] = tp.customers / len(P); tp.to_csv(D / "s7_top_paths.csv", index=False)
stable = P[YEARS].nunique(axis=1).eq(1).mean(); print("\nحاضر در 5 سال:", len(P), " ثابت در یک حالت:", round(stable, 3)); print(tp.head(12).to_string())
# شمار تغییر حالت در 4 گذار (مشتریان 5 ساله)
nch = sum((P[YEARS[i]] != P[YEARS[i + 1]]).astype(int) for i in range(4)); nch.value_counts(normalize=True).sort_index().rename_axis("changes").to_csv(D / "s7_n_changes_5yr.csv"); print("توزیع شمار تغییر:", nch.value_counts(normalize=True).sort_index().round(3).to_dict())
# سرنوشت 4 ساله‌ی هر خوشه‌ی 1400
c4 = pd.crosstab(P[1400], P[1404]).reindex(index=STATES[:-1], columns=STATES[:-1]).fillna(0).astype(int); c4.to_csv(D / "s7_aligned_1400_to_1404_counts.csv")

# ---------- نمودارها
pa = res["aligned"]["pooled"]; M = rowpct(pa).fillna(0).to_numpy()
fig, ax = plt.subplots(figsize=(10, 6.8)); im = ax.imshow(M, cmap="Blues", vmin=0, vmax=100)
ax.set_xticks(range(len(STATES))); ax.set_xticklabels(STATES); ax.set_yticks(range(len(STATES) - 1)); ax.set_yticklabels(STATES[:-1]); ax.set_xlabel("حالت سال بعد (X: غایب)"); ax.set_ylabel("حالت سال جاری")
for i in range(M.shape[0]):
    for j in range(M.shape[1]):
        if M[i, j] >= 1: ax.text(j, i, fd(f"{M[i, j]:.0f}"), ha="center", va="center", fontsize=8, color="white" if M[i, j] > 55 else "black")
cb = fig.colorbar(im, shrink=.8); cb.set_label("درصد سطری"); save(fig, "ch7_transition_pooled.png")

fig, axs = plt.subplots(1, 2, figsize=(13, 4.8), sharey=True); cols = plt.cm.tab20(np.linspace(0, 1, 12))
for ax, name, t in ((axs[0], "aligned", "هم‌ترازی چندکی"), (axs[1], "real", "ریال ثابت 12/1404")):
    sh = res[name]["sh"]; pct = sh / sh.sum() * 100; bottom = np.zeros(len(YEARS))
    for k, s in enumerate(STATES[:-1]): ax.bar([str(y) for y in YEARS], pct.loc[s], bottom=bottom, color=cols[k], label=s, width=.7); bottom += pct.loc[s].to_numpy()
    ax.set_title(t); ax.set_xticklabels([fd(y) for y in YEARS]); ax.set_ylabel("درصد مشتریان")
axs[1].legend(frameon=False, bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=9); save(fig, "ch7_state_shares_by_year.png")

fig, ax = plt.subplots(figsize=(10, 4.6)); x = np.arange(len(STATES) - 1)
sa = pd.read_csv(D / "s7_aligned_stay_rates.csv", index_col=0).mean(axis=1) * 100; sr = pd.read_csv(D / "s7_real_stay_rates.csv", index_col=0).mean(axis=1) * 100
ax.bar(x - .2, sa.reindex(STATES[:-1]), .4, color=BLUE, label="هم‌ترازی چندکی"); ax.bar(x + .2, sr.reindex(STATES[:-1]), .4, color=ORANGE, label="ریال ثابت")
ax.set_xticks(x); ax.set_xticklabels(STATES[:-1]); ax.set_ylabel("میانگین نرخ ماندن در گذارهای سالانه (٪)"); ax.legend(frameon=False); save(fig, "ch7_stay_rates.png")

# ---------- ورود به غیرجاری در سال بعد به تفکیک حالت سال جاری (وام‌گیران اصلی بدون غیرجاری)
Fi = F.set_index(["customer_id", "y"]); rows = []
for y in YEARS[:-1]:
    a = F[(F.y == y) & (F.has_primary_loan) & (F.npl_dec_r.fillna(0) == 0)][["customer_id", "has_primary_loan"]]
    nx = F[F.y == y + 1].set_index("customer_id").npl_dec_r.fillna(0)
    a = a.assign(state=SA[y].reindex(a.customer_id).to_numpy(), present=a.customer_id.isin(nx.index).to_numpy(), npl_next=(nx.reindex(a.customer_id).fillna(0).to_numpy() > 0))
    rows.append(a.assign(y=y))
R = pd.concat(rows); R = R[R.present]
out = R.groupby("state").agg(borrowers=("npl_next", "size"), npl_entry_rate=("npl_next", "mean")).reindex(STATES[:-1]); out.to_csv(D / "s7_npl_entry_by_state.csv")
print("\nورود به غیرجاری سال بعد (وام‌گیران اصلی بدون غیرجاری، حالت‌ها بر پایه‌ی هم‌ترازی؛ تجمیع 4 گذار):\n", (out.assign(npl_entry_rate=out.npl_entry_rate * 100)).round(2).to_string())
print("\nنرخ ماندن:\n", pd.read_csv(D / "s7_aligned_stay_rates.csv", index_col=0).round(3).to_string())
print("\nگذار 1403->1404 (سطری %):\n", rowpct(res["aligned"]["tr"][1403]).round(1).to_string())
print("\nسرنوشت 1400->1404 مشتریان 5 ساله (سطری %):\n", rowpct(c4).round(1).to_string())
