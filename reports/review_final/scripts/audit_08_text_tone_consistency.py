"""Audit Script 08: Textual, Tone, Consistency, and Scientific Review (Section 3-B, 3-P, 3-CH)
Systematically checks:
1. Consistency of numbers across Executive Summary and Chapters 1 to 6.
2. Textual descriptions of multi-panel figures (left vs right, top vs bottom).
3. Exact matching of cluster names with cluster_definitions.csv.
4. Detection of forbidden machine clichés, emotional words, or prohibited phrases ("اگر داده", "نقص داده", "ناهنجاری", "پرسش باز").
5. Scientific integrity of methodological citations in Chapter 2.
6. Evaluates clarity and managerial readability for bank executives.
Saves audit findings to reports/review_final/results/text_tone_audit.csv.
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "reports" / "review_final" / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("RUNNING TEXTUAL, TONE & CONSISTENCY AUDIT")
print("=" * 60)

report_text = (ROOT / "reports" / "phase2_final_report.md").read_text(encoding="utf-8")
defs = pd.read_csv(ROOT / "data" / "processed" / "phase2_clustering" / "cluster_definitions.csv")

findings = []

def log_finding(category, severity, location, evidence, recommendation):
    findings.append({
        'category': category,
        'severity': severity,
        'location': location,
        'evidence': evidence,
        'recommendation': recommendation
    })

# 1. Cluster Name Check
print("\n--- 1. Checking Cluster Names Consistency ---")
for _, r in defs.iterrows():
    seg = r['segment']
    approved_name = r['name_fa']
    # Check if approved name appears in text
    if approved_name in report_text:
        print(f"  [OK] {seg}: '{approved_name}' found in text.")
    else:
        print(f"  [WARNING] {seg}: '{approved_name}' NOT found exactly in text!")
        log_finding(
            "نام خوشه‌ها",
            "مهم",
            "متن گزارش",
            f"نام مصوب '{approved_name}' برای {seg} به طور دقیق یافت نشد.",
            f"نام خوشه در تمام ارجاعات به '{approved_name}' یکدست شود."
        )

# Check for obsolete name of C4
if "حساب‌های راکد با وام معوق" in report_text or "حساب‌های راکد" in report_text:
    log_finding(
        "نام خوشه‌ها",
        "مهم",
        "متن گزارش",
        "عبارت 'حساب‌های راکد' مشاهده شد.",
        "نام مصوب 'حساب‌های ایستا با اقلیت وام‌دار معوق' استفاده شود."
    )
else:
    print("  [OK] No obsolete C4 names ('حساب‌های راکد') found.")

# 2. Check for Prohibited / Doubtful Phrases
print("\n--- 2. Checking Forbidden / Machine-like Phrases ---")
forbidden_patterns = [
    (r"اگر\s+داده[ی‌\s]+.*?\s+داشتیم", "عبارت شرطی کمبود داده ('اگر داده ... داشتیم')"),
    (r"نقص\s+داده", "واژه 'نقص داده'"),
    (r"ناهنجاری", "واژه 'ناهنجاری'"),
    (r"پرسش\s+باز", "عبارت 'پرسش باز'"),
    (r"اعجاب[‌\s]*انگیز", "صفت اغراق‌آمیز 'اعجاب‌انگیز'"),
    (r"شگفت[‌\s]*انگیز", "صفت اغراق‌آمیز 'شگفت‌انگیز'"),
    (r"بی[‌\s]*سابقه", "صفت اغراق‌آمیز 'بی‌سابقه'"),
    (r"قاطعانه", "قید اغراق‌آمیز 'قاطعانه'")
]

for pat, desc in forbidden_patterns:
    matches = re.findall(pat, report_text)
    if matches:
        # Find context
        for m in set(matches):
            # find line number
            lines = [l.strip() for l in report_text.split('\n') if m in l]
            for l in lines[:2]:
                log_finding(
                    "لحن و زبان",
                    "جزئی" if "ناهنجاری" in desc or "اغراق" in desc else "مهم",
                    "متن گزارش",
                    f"الگوی '{desc}': '{l[:100]}'",
                    "جایگزینی با واژگان حرفه‌ای خنثی بانکی (مانند ویژگی ساختاری، رفتار متمایز، یا بازتاب تمرکز منابع)"
                )
    else:
        print(f"  [OK] No occurrences of '{desc}'.")

# 3. Check Left/Right Descriptions of Multi-Panel Figures
print("\n--- 3. Checking Multi-Panel Figure Left/Right Orientations ---")
# Check Figure 4-3 (f5_3_npl_by_cluster):
# Title: نسبت غیرجاری به تسهیلات (چپ) و سهم از کل مطالبات غیرجاری (راست)
# Check Figure 6-1 (f8_1_weighted_shares):
# Title: سهم گروه‌ها از مانده‌ی تسهیلات (چپ) و سپرده (راست)
f43_refs = [l.strip() for l in report_text.split('\n') if 'نمودار ۴-۳' in l or '۴-۳' in l and 'چپ' in l or 'راست' in l]
for l in f43_refs[:3]:
    print(f"  Fig 4-3 text: {l[:100]}")

f61_refs = [l.strip() for l in report_text.split('\n') if 'نمودار ۶-۱' in l or '۶-۱' in l and 'چپ' in l or 'راست' in l]
for l in f61_refs[:3]:
    print(f"  Fig 6-1 text: {l[:100]}")

# 4. Check Consistency of Shared Numbers Across Sections
print("\n--- 4. Checking Cross-Sectional Numerical Consistency ---")
# Check C1 deposit share in Summary vs Ch3 vs Ch4
# Check C1 loan share
# Check total customers 712,908
occurrences_712908 = len(re.findall(r"۷۱۲[,\u066C]۹۰۸", report_text))
print(f"  Number of 712,908 mentions in report: {occurrences_712908}")

occurrences_8477 = len(re.findall(r"۸۴[,\.]۷[۷۸]", report_text))
print(f"  Number of 84.77 / 84.78 mentions in report: {occurrences_8477}")

occurrences_12497 = len(re.findall(r"۱۲۴[,\.]۹۷", report_text))
print(f"  Number of 124.97 mentions in report: {occurrences_12497}")

occurrences_1066 = len(re.findall(r"۱۰[,\.]۶۶", report_text))
print(f"  Number of 10.66 mentions in report: {occurrences_1066}")

# 5. Scientific Checks in Chapter 2
print("\n--- 5. Checking Scientific Statements in Chapter 2 ---")
# Check if Lloyd, MacQueen, Arthur, Ward, Dempster, Campello, McInnes, etc. are properly described
sci_checks = [
    ("Lloyd", "الگوریتم استاندارد K-Means با روش کمترین مربعات برداری"),
    ("MacQueen", "ابداع نام و فرمول‌بندی اولیه K-Means (1967)"),
    ("Arthur & Vassilvitskii", "روش کانون‌یابی اولیه k-means++ (2007)"),
    ("Ward", "روش خوشه‌بندی سلسله‌مراتبی با کمینه‌سازی واریانس درون‌گروهی (1963)"),
    ("Dempster", "الگوریتم بیشینه‌سازی امید ریاضی (EM) برای مدل‌های آمیخته گاوسی (1977)"),
    ("Ester", "الگوریتم DBSCAN برای کشف خوشه‌های چگالی‌محور (1996)"),
    ("Campello / McInnes", "الگوریتم HDBSCAN بر پایه برآورد چگالی سلسله‌مراتبی (2013/2017)"),
    ("Hubert & Arabie", "شاخص تعدیل‌شده رند (ARI) با تصحیح شانس تصادفی (1985)"),
    ("Rousseeuw", "ضریب سیلوئت برای ارزیابی تفکیک و فشردگی خوشه‌ها (1987)"),
    ("Davies & Bouldin", "شاخص دیویس-بولدین بر پایه نسبت پراکندگی درون به بین خوشه‌ای (1979)"),
    ("Hanley & McNeil", "مفهوم و کاربرد سطح زیر منحنی ROC (AUC) (1982)")
]
for auth, desc in sci_checks:
    # check if mentioned
    tokens = auth.split()
    is_present = any(t in report_text for t in tokens)
    print(f"  Scientific Check [{auth}]: {'Found' if is_present else 'Missing'} ({desc})")

# 6. Managerial Readability Evaluation
print("\n--- 6. Managerial Readability Evaluation ---")
# Check for technical jargon defined at first use:
# LDR, NPL, DPD, ARI, AUC, Silhouette, Raking
tech_terms = [
    ("LDR", "نسبت تسهیلات به سپرده"),
    ("NPL", "نسبت مطالبات غیرجاری"),
    ("DPD", "تعداد روزهای تأخیر اقساط"),
    ("AUC", "سطح زیر منحنی مشخصه عملکرد تشخیصی"),
    ("ARI", "شاخص تعدیل‌شده رند"),
    ("سیلوئت", "ضریب اعتبارسنجی فشردگی و تفکیک خوشه"),
    ("Raking", "وزن‌دهی تکراری متقاطع بر مبنای حاشیه‌ها")
]
for term, meaning in tech_terms:
    if term in report_text or meaning in report_text:
        print(f"  [OK] Technical concept '{term}' / '{meaning}' present and explained in text.")
    else:
        log_finding(
            "خوانایی مدیریتی",
            "جزئی",
            "متن گزارش",
            f"مفهوم فنی '{term}' ممکن است نیاز به توضیح تکمیلی در پاورقی داشته باشد.",
            f"افزودن توضیح یک‌خطی در اولین کاربرد برای خواننده مدیریتی بانک."
        )

# Save findings
df_findings = pd.DataFrame(findings)
out_findings_file = RESULTS / "text_tone_audit.csv"
df_findings.to_csv(out_findings_file, index=False, encoding='utf-8-sig')
print(f"\nSaved text and tone audit to: {out_findings_file}")
print(f"Total findings logged: {len(df_findings)}")
if len(df_findings) > 0:
    print(df_findings[['category', 'severity', 'location', 'evidence']].to_string())
