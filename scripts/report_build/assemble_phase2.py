# -*- coding: utf-8 -*-
"""Assemble reports/phase2_final_report.md from reports/phase2_report_src/*.md with automatic numbering.

Tokens in the sources:
  {{FIG:key|عنوان}}    نمودار (key = نام فایل بدون پسوند در reports/figures/phase2_final)؛ عنوان زیر نمودار می‌آید
  {{TABLE:key}}        جدول از reports/tables_phase2/<key>.md (عنوان همان فایل، شماره‌ی خودکار)
  {{TABLE:key|عنوان}}  همان با عنوان دلخواه
  {{TCAP:key|عنوان}}   فقط عنوان شماره‌دار برای جدولی که در خود متن نوشته شده است
  {{R:key}}            ارجاع در متن: «نمودار ۲-۳» یا «جدول ۲-۱» (شماره‌ها از ترتیب ظهور در فصل)
Numbering restarts in every chapter ('# فصل N'); appendices use the letter ('# پیوست الف: ...'); sections without chapter (summary) get no number.
Run: python scripts/report_build/assemble_phase2.py"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "reports" / "phase2_report_src"; TAB = ROOT / "reports" / "tables_phase2"
ORDER = ["ch0_front.md", "ch0_summary.md", "ch1.md", "ch2.md", "ch3.md", "ch4.md", "ch5.md", "ch6.md", "ch7_request.md", "appendix.md", "refs.md"]
FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
fd = lambda s: str(s).translate(FA)

text = "\n".join(p.read_text(encoding="utf-8").rstrip() + "\n" for p in (SRC / f for f in ORDER) if p.exists())
tok = re.compile(r"\{\{(FIG|TABLE|TCAP):([A-Za-z0-9_]+)(?:\|([^}]*))?\}\}")
# --- گذر نخست: شماره‌ی هر نمودار و جدول
num, label = {}, None
counters = {"f": 0, "t": 0}
for line in text.split("\n"):
    h = re.match(r"^# (فصل ([۰-۹]+)|پیوست ([^:]+)):", line)
    if h:
        label = fd(h.group(2)) if h.group(2) else h.group(3).strip(); counters = {"f": 0, "t": 0}
    elif re.match(r"^# ", line):
        label = None; counters = {"f": 0, "t": 0}
    for m in tok.finditer(line):
        kind = "f" if m.group(1) == "FIG" else "t"; counters[kind] += 1
        num[m.group(2)] = (kind, f"{label}-{fd(counters[kind])}" if label else None)
def name(key):
    kind, n = num[key]; w = "نمودار" if kind == "f" else "جدول"
    return f"{w} {n}" if n else w

# --- گذر دوم: جای‌گذاری
def rep(m):
    kind, key, title = m.group(1), m.group(2), m.group(3)
    if kind == "FIG":
        cap = f"{name(key)}: {title}" if num[key][1] else title
        return f"![{cap}](figures/phase2_final/{key}.png)\n\n**{cap}**"
    if kind == "TCAP":
        return f"**{name(key)}: {title}**" if num[key][1] else f"**{title}**"
    t = (TAB / f"{key}.md").read_text(encoding="utf-8").rstrip()
    first, rest = t.split("\n", 1)
    old = re.match(r"\*\*(?:جدول [^:]*:\s*)?(.+?)\*\*", first).group(1)
    cap = title or old
    return f"**{name(key)}: {cap}**\n{rest}" if num[key][1] else f"**{cap}**\n{rest}"
text = tok.sub(rep, text)
text = re.sub(r"\{\{R:([A-Za-z0-9_]+)\}\}", lambda m: name(m.group(1)), text)
(ROOT / "reports" / "phase2_final_report.md").write_text(text, encoding="utf-8")
words = len(re.findall(r"\S+", text)); print("assembled; words:", words, "; figures:", sum(1 for v in num.values() if v[0] == "f"), "tables:", sum(1 for v in num.values() if v[0] == "t"))
