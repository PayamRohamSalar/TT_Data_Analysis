# -*- coding: utf-8 -*-
"""ممیزی واحد پولی: جدول‌ها و جمله‌های دارای «هزار میلیارد تومان» نباید مقداری بزرگ‌تر از سقف منطقی داشته باشند.

سقف: بزرگ‌ترین مانده‌ی کل بانک ۱۴۸.۲ هزار میلیارد تومان است؛ مقدار بالاتر از ۱۵۰ در ستون مبلغ نشانه‌ی ریال است.
اجرا: python scripts/report_build/audit_units.py
"""
import re
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "reports" / "phase1_final_report.md"
TR = str.maketrans("۰۱۲۳۴۵۶۷۸۹٫٬", "0123456789..")
SKIP_COL = re.compile(r"تعداد|مشتری|حساب|قرارداد|قسط|شعبه|ریال|سال|مقطع|٪|درصد|نسبت|سهم|رشد|پوشش|اختلاف|میانگین مانده|میلیون|عمر|بازه|وضعیت|نوع|بخش|استان|گروه|کوهورت|صدک|گذار|شاخص|مبنا|کد|ردیف|اولویت|داده|کاربرد|فصل")
LIM = 150.0


def num(s):
    s = s.translate(TR).replace(",", "").replace("*", "").strip()
    m = re.fullmatch(r"-?[0-9]+(?:\.[0-9]+)?", s)
    return float(s) if m else None


def main():
    lines = SRC.read_text(encoding="utf-8").split("\n")
    probs = []
    i = 0
    while i < len(lines):
        l = lines[i]
        if l.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
            hdr = [c.strip() for c in l.strip().strip("|").split("|")]
            cap = ""
            for k in range(i - 1, max(i - 4, 0), -1):
                if lines[k].startswith("**جدول"):
                    cap = lines[k]
                    break
            j = i + 2
            rows = []
            while j < len(lines) and lines[j].startswith("|"):
                rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")])
                j += 1
            unit_tbl = "هزار میلیارد تومان" in cap or any("هزار میلیارد تومان" in h for h in hdr)
            rial_col = [("ریال" in h and "تومان" not in h) for h in hdr]
            if unit_tbl:
                for r in rows:
                    for ci, c in enumerate(r):
                        if ci >= len(hdr):
                            continue
                        if SKIP_COL.search(hdr[ci]) and "هزار میلیارد تومان" not in hdr[ci]:
                            continue
                        v = num(c)
                        if v is not None and v > LIM and not rial_col[ci]:
                            probs.append(f"خط {i + 1}: جدول «{cap[:40]}» ستون «{hdr[ci][:30]}» مقدار {c}")
            i = j
            continue
        i += 1
    for k, l in enumerate(lines, 1):
        for m in re.finditer(r"([۰-۹][۰-۹,]*(?:\.[۰-۹]+)?)\s*هزار میلیارد تومان", l):
            v = num(m.group(1))
            if v is not None and v > LIM:
                probs.append(f"خط {k}: متن «{m.group(0)}»")
        for m in re.finditer(r"([۰-۹][۰-۹,]*(?:\.[۰-۹]+)?)\s*هزار میلیارد ریال", l):
            v = num(m.group(1))
            if v is not None and v < 100 and "ریال" in l and "تبدیل" not in l:
                probs.append(f"(بررسی) خط {k}: مقدار کوچک با واحد ریال «{m.group(0)}»")
    print("موارد:", len(probs))
    for p in probs:
        print(p)
    return 1 if probs else 0


if __name__ == "__main__":
    sys.exit(main())
