# -*- coding: utf-8 -*-
"""اعتبارسنجی ارجاع‌های بخش/جدول/نمودار و ترتیب شماره‌گذاری در reports/phase1_final_report.md.

اجرا: python scripts/report_build/check_refs.py
خروجی: فهرست ارجاع‌های بی‌مقصد، شماره‌های تکراری/ناپیوسته و جدول‌ها یا نمودارهای ارجاع‌نشده.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "reports" / "phase1_final_report.md"
FIG = ROOT / "reports" / "figures" / "phase1_market_overview"
TR = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")


def e(s):
    return s.translate(TR)


def main():
    lines = SRC.read_text(encoding="utf-8").split("\n")
    sections, tables, figs, chapters = {}, {}, {}, set()
    for i, l in enumerate(lines, 1):
        m = re.match(r"^(#{2,3}) ([۰-۹]+(?:\.[۰-۹]+)+)\s", l)
        if m:
            sections.setdefault(e(m.group(2)), []).append(i)
        m = re.match(r"^# فصل ([۰-۹]+)", l)
        if m:
            chapters.add(int(e(m.group(1))))
        m = re.match(r"^\*\*جدول ([۰-۹]+-[۰-۹]+):", l)
        if m:
            tables.setdefault(e(m.group(1)), []).append(i)
        m = re.match(r"^!\[نمودار ([۰-۹]+-[۰-۹]+):[^\]]*\]\(([^)]+)\)", l)
        if m:
            figs.setdefault(e(m.group(1)), []).append((i, m.group(2)))
    problems = []
    for k, v in sections.items():
        if len(v) > 1:
            problems.append(f"بخش تکراری {k}: خطوط {v}")
    for k, v in tables.items():
        if len(v) > 1:
            problems.append(f"جدول تکراری {k}: خطوط {v}")
    for k, v in figs.items():
        if len(v) > 1:
            problems.append(f"نمودار تکراری {k}: خطوط {[x[0] for x in v]}")
        if not (FIG / Path(v[0][1]).name).exists():
            problems.append(f"فایل نمودار {k} وجود ندارد: {v[0][1]}")
    # ترتیب پیوسته‌ی جدول و نمودار در هر فصل
    for kind, reg in (("جدول", tables), ("نمودار", figs)):
        per = {}
        for k in reg:
            a, b = k.split("-")
            per.setdefault(int(a), []).append(int(b))
        for ch, nums in per.items():
            nums.sort()
            if nums != list(range(1, len(nums) + 1)):
                problems.append(f"{kind} فصل {ch} ناپیوسته: {nums}")
    # ارجاع‌ها
    used_t, used_f, used_s = set(), set(), set()
    for i, l in enumerate(lines, 1):
        if l.startswith("**جدول ") or l.startswith("!["):
            body = re.sub(r"^\*\*جدول [۰-۹]+-[۰-۹]+:", "", l)
            body = re.sub(r"^!\[نمودار [۰-۹]+-[۰-۹]+:", "", body)
        else:
            body = l
        b = e(body)
        for m in re.finditer(r"جدول(?:‌های)?\s+([0-9]+-[0-9]+(?:\s*(?:،|و|تا)\s*[0-9]+-[0-9]+)*)", b):
            for n in re.findall(r"[0-9]+-[0-9]+", m.group(1)):
                used_t.add(n)
                if n not in tables:
                    problems.append(f"خط {i}: ارجاع به جدول ناموجود {n}")
        for m in re.finditer(r"نمودار(?:های)?\s+([0-9]+-[0-9]+(?:\s*(?:،|و|تا)\s*[0-9]+-[0-9]+)*)", b):
            for n in re.findall(r"[0-9]+-[0-9]+", m.group(1)):
                used_f.add(n)
                if n not in figs:
                    problems.append(f"خط {i}: ارجاع به نمودار ناموجود {n}")
        for m in re.finditer(r"بخش(?:‌های)?\s+([0-9]+\.[0-9]+(?:\.[0-9]+)?(?:\s*(?:،|و|تا)\s*[0-9]+\.[0-9]+(?:\.[0-9]+)?)*)", b):
            for n in re.findall(r"[0-9]+\.[0-9]+(?:\.[0-9]+)?", m.group(1)):
                used_s.add(n)
                if n not in sections:
                    problems.append(f"خط {i}: ارجاع به بخش ناموجود {n}")
        for m in re.finditer(r"فصل(?:‌های)?\s+([0-9]+(?:\s*(?:،|و|تا)\s*[0-9]+)*)", b):
            for n in re.findall(r"[0-9]+", m.group(1)):
                if int(n) not in chapters:
                    problems.append(f"خط {i}: ارجاع به فصل ناموجود {n}")
    for k in sorted(tables):
        if k not in used_t:
            problems.append(f"(اطلاعی) جدول {k} در متن ارجاع نشده است (خط {tables[k][0]})")
    for k in sorted(figs):
        if k not in used_f:
            problems.append(f"(اطلاعی) نمودار {k} در متن ارجاع نشده است (خط {figs[k][0][0]})")
    print(f"بخش‌ها: {len(sections)}، جدول‌ها: {len(tables)}، نمودارها: {len(figs)}، فصل‌ها: {sorted(chapters)}")
    for p in problems:
        print(p)
    print("جمع موارد:", len(problems))
    return 1 if any(not p.startswith("(اطلاعی)") for p in problems) else 0


if __name__ == "__main__":
    sys.exit(main())
