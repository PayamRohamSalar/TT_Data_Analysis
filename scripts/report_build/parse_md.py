# -*- coding: utf-8 -*-
"""Markdown (reports/phase1_final_report.md) -> typed blocks (JSON) for the Word and Excel builders.

Run:  python scripts/report_build/parse_md.py
Output: scripts/report_build/.cache/report_blocks.json
"""
import io
import json
import re
import struct
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
import sys
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "reports" / "phase1_final_report.md"
FIG_DIR = ROOT / "reports" / "figures" / ("phase2_final" if "phase2" in str(SRC) else "phase1_market_overview")
CACHE = Path(__file__).resolve().parent / ".cache"
CACHE.mkdir(exist_ok=True)

INLINE_RE = re.compile(r"(\*\*.+?\*\*|`[^`]+`|(?<![*\w])\*[^*\n]+?\*(?![*\w]))")
CODE_RE = re.compile(r"(`[^`]+`)")
IMAGE_RE = re.compile(r"!\[(.*?)\]\(([^)]+)\)")


def parse_inline(text):
    runs, pos = [], 0
    for m in INLINE_RE.finditer(text):
        if m.start() > pos:
            runs.append({"text": text[pos:m.start()], "bold": False, "code": False})
        tok = m.group(0)
        if tok.startswith("**"):
            inner = tok[2:-2]
            for part in CODE_RE.split(inner):
                if part == "":
                    continue
                if part.startswith("`") and part.endswith("`") and len(part) > 2:
                    runs.append({"text": part[1:-1], "bold": True, "code": True})
                else:
                    runs.append({"text": part, "bold": True, "code": False})
        elif tok.startswith("`"):
            runs.append({"text": tok[1:-1], "bold": False, "code": True})
        else:  # *italic* -> متن ساده بدون ستاره
            runs.append({"text": tok[1:-1], "bold": False, "code": False})
        pos = m.end()
    if pos < len(text):
        runs.append({"text": text[pos:], "bold": False, "code": False})
    return runs or [{"text": "", "bold": False, "code": False}]


def is_table_row(line):
    s = line.strip()
    return s.startswith("|") and s.endswith("|")


def is_sep_row(line):
    cells = line.strip().strip("|").split("|")
    return all(re.fullmatch(r"\s*:?-+:?\s*", c) for c in cells)


def split_row(line):
    s = line.strip()
    s = s[1:] if s.startswith("|") else s
    s = s[:-1] if s.endswith("|") else s
    return [c.strip() for c in s.split("|")]


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])


def main():
    lines = io.open(SRC, encoding="utf-8-sig").read().split("\n")
    blocks, i, n = [], 0, len(lines)
    while i < n:
        line = lines[i]
        st = line.strip()
        if st == "":
            i += 1
            continue
        if st == "---":
            blocks.append({"type": "hr"})
            i += 1
            continue
        if st.startswith("$$") and st.endswith("$$") and len(st) > 4:
            blocks.append({"type": "equation", "text": st[2:-2].strip()})
            i += 1
            continue
        img = st[1:].strip() if st.startswith(">") else st
        m = IMAGE_RE.match(img)
        if m:
            src = FIG_DIR / Path(m.group(2)).name
            w, h = png_size(src) if src.exists() else (0, 0)
            alt = m.group(1); i += 1
            j = i
            while j < n and lines[j].strip() == "":
                j += 1
            if j < n and re.match(r"^\*\*نمودار .*\*\*$", lines[j].strip()):   # عنوان زیر نمودار (خط پررنگ پس از تصویر) جایگزین alt می‌شود
                alt = lines[j].strip()[2:-2]; i = j + 1
            blocks.append({"type": "image", "alt": alt, "src": m.group(2), "exists": src.exists(), "w": w, "h": h})
            continue
        hm = re.match(r"^(#{1,3})\s+(.*)$", st)
        if hm:
            blocks.append({"type": "heading", "level": len(hm.group(1)), "runs": parse_inline(hm.group(2))})
            i += 1
            continue
        if is_table_row(line) and i + 1 < n and is_table_row(lines[i + 1]) and is_sep_row(lines[i + 1]):
            header = split_row(line)
            aligns = []
            for c in split_row(lines[i + 1]):
                c = c.strip()
                aligns.append("center" if c.startswith(":") and c.endswith(":") else "left" if c.startswith(":") else "right")
            j, rows = i + 2, []
            while j < n and is_table_row(lines[j]):
                rows.append(split_row(lines[j]))
                j += 1
            blocks.append({"type": "table", "header": [parse_inline(c) for c in header], "aligns": aligns,
                           "rows": [[parse_inline(c) for c in r] for r in rows]})
            i = j
            continue
        if st.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip()[1:].strip())
                i += 1
            blocks.append({"type": "blockquote", "runs": parse_inline(" ".join(x for x in buf if x))})
            continue
        lm = re.match(r"^([۰-۹0-9]+)[.\)]\s+(.*)$", st)
        if lm:
            blocks.append({"type": "list_item", "ordered": True, "marker": lm.group(1), "runs": parse_inline(lm.group(2))})
            i += 1
            continue
        if st.startswith(("- ", "* ")):
            blocks.append({"type": "list_item", "ordered": False, "runs": parse_inline(st[2:])})
            i += 1
            continue
        buf = [line]
        i += 1
        while (i < n and lines[i].strip() != "" and not is_table_row(lines[i])
               and not lines[i].strip().startswith(("#", ">", "---", "$$", "![", "- ", "* "))
               and not re.match(r"^([۰-۹0-9]+)[.\)]\s+", lines[i].strip())):
            buf.append(lines[i])
            i += 1
        blocks.append({"type": "para", "runs": parse_inline(" ".join(x.strip() for x in buf))})
    (CACHE / "report_blocks.json").write_text(json.dumps(blocks, ensure_ascii=False), encoding="utf-8")
    print("blocks:", len(blocks), dict(Counter(b["type"] for b in blocks)))
    missing = [b["src"] for b in blocks if b["type"] == "image" and not b["exists"]]
    print("missing images:", missing)


if __name__ == "__main__":
    main()
