"""فاز ۲ - S10: خروجی‌های تحویلی به فازهای ۳ و ۴ (بدون DB؛ فایل‌محور).
ورودی: features_customer_year.pkl، panel_customer_year.pkl، cluster_assignments_1404.pkl، s5_final_centers.json، prep_spec_v2.json، لنزها، جدول‌های S6 تا S9.
خروجی (data/processed/phase2_clustering/): customer_cluster_assignments.csv.gz (مشتری-سال)، customer_cluster_attributes_1404.csv.gz، cluster_definitions.csv، cluster_profiles.csv،
cluster_transition_matrices.csv، cluster_state_counts_by_year.csv، cluster_model_spec.json، generalization_weights.csv، README_outputs.md (تولید دستی در بخش پایانی با اعتبارسنجی)."""
import json, shutil
from pathlib import Path
import numpy as np, pandas as pd
from tt_bank.phase2_clustering.prep import Prep

ROOT = Path(__file__).resolve().parents[2]; D = ROOT / "data" / "processed" / "phase2_clustering"
YEARS = [1400, 1401, 1402, 1403, 1404]; STATES = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "T", "I", "N", "S"]
NAME = {"C1": "مشتریان کلان", "C2": "وام‌گیران عمده", "C3": "سپرده‌گذاران در حال رشد", "C4": "حساب‌های ایستا",
        "C5": "سپرده‌گذاران خرد فعال", "C6": "سپرده‌گذاران خرد کم‌فعال", "C7": "وام‌گیران پرریسک", "C8": "وام‌گیران منظم",
        "T": "وام‌گیران با سپرده‌ی خدماتی", "I": "بی‌فعالیت", "N": "نوپا", "S": "نهادی"}
RULE = {"C1": "خوشه‌ی K-Means (مدل نهایی S5)", "C2": "خوشه‌ی K-Means", "C3": "خوشه‌ی K-Means", "C4": "خوشه‌ی K-Means", "C5": "خوشه‌ی K-Means", "C6": "خوشه‌ی K-Means", "C7": "خوشه‌ی K-Means", "C8": "خوشه‌ی K-Means",
        "T": "وام‌گیر اصلی و (کمتر از 3 ماه گردش یا بیشینه‌ی مانده کمتر از 5 میلیون ریال)؛ قاعده‌ای، بیرون از خوشه‌بندی", "I": "بی‌فعالیت دست‌کم 6 ماه بدون وام، با گردش کم یا مانده‌ی ناچیز؛ قاعده‌ای",
        "N": "نخستین ردیف در همان سال و کمتر از 6 ماه سابقه؛ قاعده‌ای", "S": "دست‌کم 100 حساب در یکی از ماه‌های سال؛ قاعده‌ای"}
DEP_LENS = {1: "سپرده‌گذاران بزرگ و فعال", 2: "سپرده‌گذاران میان‌رده‌ی رو به کاهش", 3: "سپرده‌گذاران خرد رو به رشد", 4: "حساب‌های ایستا", 5: "حساب‌های تقریباً خالی"}
CRED_LENS = {1: "وام‌گیران بخش مسکن", 2: "وام‌گیران بدهکار با سپرده‌ی تهی", 3: "وام‌گیران مرابحه‌ی پرنرخ بخش خدمات", 4: "وام‌گیران قرض‌الحسنه"}

F = pd.read_pickle(D / "features_customer_year.pkl")
pan = pd.read_pickle(D / "panel_customer_year.pkl")[["customer_id", "y", "bal_max"]]; F = F.merge(pan, on=["customer_id", "y"], how="left")
F["token_borrower"] = (F.category == "model") & F.has_primary_loan & ((F.turn_months < 3) | (F.bal_max < 5e6))
prep = Prep.from_json(D / "prep_spec_v2.json"); C = np.array(json.load(open(D / "s5_final_centers.json"))["centers_std"], dtype="float32")

def assign(df, aligned):
    X = prep.transform(df, aligned=aligned).astype("float32")
    return ((X ** 2).sum(1)[:, None] - 2 * X @ C.T + (C ** 2).sum(1)[None, :]).argmin(1) + 1
def states(aligned):
    out = []
    for y in YEARS:
        g = F[F.y == y].reset_index(drop=True); st = pd.Series("I", index=g.index)
        st[g.category == "institutional_candidate"] = "S"; st[g.category == "newcomer"] = "N"; st[g.category == "idle_token"] = "I"; st[g.token_borrower] = "T"
        m = ((g.category == "model") & ~g.token_borrower).to_numpy(); st[m] = ["C%d" % k for k in assign(g[m], aligned)]
        out.append(pd.DataFrame({"customer_id": g.customer_id.to_numpy(), "year": y, "segment": st.to_numpy()}))
    return pd.concat(out, ignore_index=True)
SA = states(True).rename(columns={"segment": "segment"}); SR = states(False).rename(columns={"segment": "segment_real_rial"})

# ---------- customer_cluster_assignments (مشتری-سال)
base = F[["customer_id", "y", "obs_months", "category", "relationship", "has_loan_dec", "bal_dec", "loan_dec_r", "npl_dec_r", "province", "home_branch"]].rename(columns={"y": "year"})
A = base.merge(SA, on=["customer_id", "year"]).merge(SR, on=["customer_id", "year"])
A["group"] = A.category.map({"model": "model", "idle_token": "idle", "newcomer": "newcomer", "institutional_candidate": "institutional"}).fillna("other")
A.loc[A.segment == "T", "group"] = "token_borrower"
A["cluster"] = A.segment.str[1:].where(A.segment.str.startswith("C"), "0").astype(int)
A = A.sort_values(["customer_id", "year"]).reset_index(drop=True)
g = A.groupby("customer_id")
A["prev_segment"] = g.segment.shift(1).where(g.year.shift(1) == A.year - 1, "X").where(A.year > 1400, "")
A["next_segment"] = g.segment.shift(-1).where(g.year.shift(-1) == A.year + 1, "X").where(A.year < 1404, "")
A["bal_dec"] = A.bal_dec.fillna(0).round(0); A["loan_dec_r"] = A.loan_dec_r.fillna(0).round(0); A["npl_dec_r"] = A.npl_dec_r.fillna(0).round(0)
cols = ["customer_id", "year", "segment", "cluster", "group", "segment_real_rial", "prev_segment", "next_segment", "relationship", "has_loan_dec", "bal_dec", "loan_dec_r", "npl_dec_r", "province", "home_branch"]
h = (A.customer_id.astype("int64").to_numpy() * 2654435761 % 2 ** 32) / 2 ** 32   # تقسیم قطعی بر پایه‌ی شناسه (یک مشتری در همه‌ی سال‌ها یک گروه)
A["split_group"] = np.where(h < .70, "train", np.where(h < .85, "val", "test"))
cols = cols[:2] + ["obs_months"] + cols[2:] + ["split_group"]
A = A[cols]; A.to_csv(D / "customer_cluster_assignments.csv.gz", index=False, compression="gzip")
print("assignments", A.shape, " کلید یکتا:", not A.duplicated(["customer_id", "year"]).any())

# ---------- ویژگی‌های 1404 برای فاز 3 (استان، شعبه، بخش اقتصادی، لنزها)
dl = pd.read_pickle(D / "deposit_lens_labels_1404.pkl"); cl = pd.read_pickle(D / "credit_lens_v2_labels_1404.pkl")
X4 = F[F.y == 1404].merge(A[A.year == 1404][["customer_id", "segment", "cluster"]], on="customer_id").merge(dl, on="customer_id", how="left").merge(cl, on="customer_id", how="left")
keep = ["customer_id", "segment", "cluster", "deposit_lens", "credit_lens", "category", "relationship", "province", "home_branch", "home_source", "tenure_months", "obs_months",
        "bal_dec", "bal_mean_r", "bal_end_r", "bal_max_r", "cr_sum_r", "db_sum_r", "crn_sum", "dbn_sum", "turn_share", "bal_cv", "bal_trend", "drawdown", "acc_mean",
        "has_loan_dec", "has_primary_loan", "loan_dec_r", "npl_dec_r", "n_loan_dec", "loan_to_dep", "npl_share", "late30_share", "late90_share", "has_ledger",
        "rate_w", "coll_w", "duration_w", "ltype_qard", "ltype_murabaha", "ltype_partnership", "ltype_installment", "sector_services", "sector_industry", "sector_housing", "sector_agri", "sector_trade", "sector_other_sector",
        "has_interest", "interest_sum_r", "interest_rate_r", "share_long_k", "share_short_k", "share_qard_k", "share_current_k", "share_special_k", "has_blocked_account"]
X4 = X4.rename(columns={"deposit_lens": "deposit_lens", "credit_lens": "credit_lens"})[[c for c in keep if c in X4.columns]]
X4.to_csv(D / "customer_cluster_attributes_1404.csv.gz", index=False, compression="gzip"); print("attributes_1404", X4.shape)

# ---------- تعریف و پروفایل خوشه‌ها
cnt = A[A.year == 1404].segment.value_counts()
defs = pd.DataFrame({"segment": STATES, "name_fa": [NAME[s] for s in STATES], "rule": [RULE[s] for s in STATES], "customers_1404": [int(cnt.get(s, 0)) for s in STATES]})
defs["in_clustering"] = defs.segment.str.startswith("C"); defs.to_csv(D / "cluster_definitions.csv", index=False, encoding="utf-8-sig")
prof = pd.read_csv(D / "cluster_profiles_1404.csv"); prof["segment"] = prof.segment.replace({"O": "I"})
prof = prof.groupby("segment", as_index=False).first() if prof.segment.duplicated().any() else prof
t61 = pd.read_csv(D / "s6_table_6_1.csv")[["segment", "share_deposit", "share_loan", "share_npl", "npl_ratio", "loan_to_deposit", "interest_coverage", "interest_per_deposit"]].add_prefix("s6_").rename(columns={"s6_segment": "segment"})
prof = prof.merge(t61, on="segment", how="left", suffixes=("", "_dup")); prof.insert(1, "name_fa", prof.segment.map(NAME))
prof = prof.set_index("segment").reindex(STATES).reset_index(); prof.to_csv(D / "cluster_profiles.csv", index=False, encoding="utf-8-sig"); print("profiles", prof.shape)

# ---------- ماتریس‌های گذار (بلند) و شمار حالت‌ها
rows = []
for var in ("aligned", "real"):
    for tag in ["pooled"] + [f"{y}_{y + 1}" for y in YEARS[:-1]]:
        c = pd.read_csv(D / f"s7_{var}_transition_{tag}_counts.csv", index_col=0)
        for fr in c.index:
            tot = c.loc[fr].sum()
            for to in c.columns:
                rows.append(dict(variant="quantile_aligned" if var == "aligned" else "real_rial_cpi", period=tag, from_state=fr, to_state=to, customers=int(c.loc[fr, to]), row_pct=round(100 * c.loc[fr, to] / tot, 3) if tot else np.nan))
TM = pd.DataFrame(rows); TM.to_csv(D / "cluster_transition_matrices.csv", index=False); print("transitions", TM.shape)
cb = []
for var, col in (("quantile_aligned", "segment"), ("real_rial_cpi", "segment_real_rial")):
    t = A.groupby(["year", col]).size().rename("customers").reset_index().rename(columns={col: "state"}); t["variant"] = var; cb.append(t)
pd.concat(cb)[["variant", "year", "state", "customers"]].to_csv(D / "cluster_state_counts_by_year.csv", index=False)

# ---------- مشخصات مدل و وزن‌های تعمیم
spec = json.load(open(D / "s5_final_centers.json")); spec["prep_spec_file"] = "prep_spec_v2.json"; spec["assignment_rule"] = "فاصله‌ی اقلیدسی تا نزدیک‌ترین مرکز در فضای استاندارد و وزن‌دار بلوک (centers_std)"
spec["token_borrower_rule"] = "category=model و وام‌گیر اصلی و (turn_months<3 یا bal_max<5e6 ریال)"; spec["institutional_rule"] = ">=100 حساب در یکی از ماه‌های سال"
spec["newcomer_rule"] = "نخستین ردیف در همان سال و کمتر از 6 ماه"; spec["cluster_names_fa"] = NAME
spec["lens_names"] = {"deposit_lens_k5": DEP_LENS, "credit_lens_v2_k4": CRED_LENS}
json.dump(spec, open(D / "cluster_model_spec.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
shutil.copy(D / "prep_spec_v2.json", D / "prep_spec_v2_handoff.json") if False else None
pw = pd.read_csv(D / "s9_province_weights.csv")[["province", "official_resources", "official_loans", "dep_s", "loan_s", "w_dep", "w_loan"]]
pw.columns = ["province", "official_resources_rial", "official_loans_rial", "sample_deposit_rial", "sample_loan_rial", "weight_deposit", "weight_loan"]
lb = pd.read_csv(D / "s9_loan_band_test.csv"); lb_out = lb[["label", "n", "bank_n", "ratio", "w"]].rename(columns={"n": "sample_borrowers", "bank_n": "bank_borrowers", "ratio": "sample_to_bank", "w": "band_weight"}); lb_out.insert(0, "table", "loan_band")
pw.insert(0, "table", "province"); pd.concat([pw, lb_out], ignore_index=True).to_csv(D / "generalization_weights.csv", index=False, encoding="utf-8-sig")

# ---------- اعتبارسنجی
chk = pd.read_pickle(D / "cluster_assignments_1404.pkl").set_index("customer_id").segment.replace({"O": "I"})
a4 = A[A.year == 1404].set_index("customer_id").segment
print("تطابق 1404 با S5: %.5f" % (a4.reindex(chk.index) == chk).mean(), " شمار 1404:", len(a4))
print("جمع هر ماتریس تجمعی aligned:", TM[(TM.variant == "quantile_aligned") & (TM.period == "pooled")].customers.sum())
print("شمار مشتری-سال:", {y: int((A.year == y).sum()) for y in YEARS}); print(A[A.year == 1404].segment.value_counts().to_dict())
print("نمونه prev/next:\n", A[A.customer_id == A.customer_id.iloc[1000]][["year", "segment", "prev_segment", "next_segment"]].to_string())
for f in ["customer_cluster_assignments.csv.gz", "customer_cluster_attributes_1404.csv.gz", "cluster_definitions.csv", "cluster_profiles.csv", "cluster_transition_matrices.csv", "cluster_state_counts_by_year.csv", "cluster_model_spec.json", "generalization_weights.csv"]:
    print(f, round((D / f).stat().st_size / 1e6, 2), "MB")
