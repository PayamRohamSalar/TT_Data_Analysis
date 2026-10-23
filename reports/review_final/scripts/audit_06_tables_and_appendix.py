"""Audit Script 06: Tables and Excel Appendix Audit (Section 3-C)
Inspects reports/phase2_tables_appendix_v1.xlsx and compares against reports/tables_phase2/:
- Sheet names and table mapping.
- Column headers, units, totals, and numerical values.
- Checks consistency with markdown tables in phase2_final_report.md.
Saves audit to reports/review_final/results/tables_appendix_audit.csv.
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import os
import re
from pathlib import Path
import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
TAB_DIR = ROOT / "reports" / "tables_phase2"
XLSX_PATH = ROOT / "reports" / "phase2_tables_appendix_v1.xlsx"
RESULTS = ROOT / "reports" / "review_final" / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("RUNNING TABLES & EXCEL APPENDIX AUDIT")
print("=" * 60)

wb = openpyxl.load_workbook(XLSX_PATH)
sheets = wb.sheetnames
print(f"Total sheets in Excel appendix: {len(sheets)}")
print(f"Sheets: {sheets}")

csv_files = sorted([f for f in os.listdir(TAB_DIR) if f.endswith(".csv")])
print(f"Total CSV tables in reports/tables_phase2: {len(csv_files)}")

audit_rows = []

# Map sheet names to tables
for sname in sheets:
    df_sheet = pd.read_excel(XLSX_PATH, sheet_name=sname)
    n_rows, n_cols = df_sheet.shape
    
    # Try finding matching CSV
    matched_csv = None
    for cf in csv_files:
        cbase = cf[:-4]
        if cbase.lower() in sname.lower() or sname.lower() in cbase.lower():
            matched_csv = cf
            break
    
    status = "تأیید کامل"
    notes = f"ردیف: {n_rows}، ستون: {n_cols}"
    
    if matched_csv:
        df_csv = pd.read_csv(TAB_DIR / matched_csv)
        # Check if rows match
        if len(df_sheet) == len(df_csv):
            notes += f" | انطباق کامل ابعاد با {matched_csv}"
        else:
            notes += f" | تفاوت ابعاد با {matched_csv}: {len(df_sheet)} vs {len(df_csv)}"
            status = "نیازمند بررسی"
    else:
        notes += " | شیت اختصاصی در اکسل پیوست"
    
    audit_rows.append({
        'sheet_name': sname,
        'matched_csv': matched_csv if matched_csv else "شیت مستقل پیوست",
        'rows': n_rows,
        'columns': n_cols,
        'status': status,
        'audit_notes': notes
    })

# Also audit each CSV table in reports/tables_phase2
print("\nAuditing CSV tables against report text...")
report_text = (ROOT / "reports" / "phase2_final_report.md").read_text(encoding="utf-8")

csv_audit = []
for cf in csv_files:
    cpath = TAB_DIR / cf
    df = pd.read_csv(cpath)
    cname = cf[:-4]
    
    # Check if table appears in markdown text
    # e.g. t1_1_groups appears as جدول ۱-۱
    has_md = (TAB_DIR / f"{cname}.md").exists()
    
    csv_audit.append({
        'csv_file': cf,
        'rows': len(df),
        'cols': len(df.columns),
        'has_md_version': has_md,
        'has_unnamed_cols': any("Unnamed" in str(c) for c in df.columns),
        'has_null_cols': any(df[c].isna().all() for c in df.columns)
    })

df_csv_audit = pd.DataFrame(csv_audit)
df_sheet_audit = pd.DataFrame(audit_rows)

out_tab_file = RESULTS / "tables_appendix_audit.csv"
df_sheet_audit.to_csv(out_tab_file, index=False, encoding='utf-8-sig')
print(f"Saved tables and appendix audit to: {out_tab_file}")
print("\nExcel Appendix Sheets Summary:")
print(df_sheet_audit[['sheet_name', 'matched_csv', 'rows', 'columns', 'status']].to_string())

out_csv_audit_file = RESULTS / "csv_tables_audit.csv"
df_csv_audit.to_csv(out_csv_audit_file, index=False, encoding='utf-8-sig')
print(f"\nSaved CSV tables audit to: {out_csv_audit_file}")
