"""فاز ۲ - گام الف-۰: ستون‌ها و نوع داده‌ی جدول‌های مرتبط (فقط خواندن؛ یک Engine)."""
from pathlib import Path
import pandas as pd
from tt_bank.db.connection import get_engine
OUT = Path(__file__).resolve().parents[2] / "data" / "processed" / "phase2_clustering"
e = get_engine()
df = pd.read_sql("""SELECT TABLE_NAME t, COLUMN_NAME c, DATA_TYPE d FROM INFORMATION_SCHEMA.COLUMNS
 WHERE TABLE_SCHEMA='dbo' ORDER BY TABLE_NAME, ORDINAL_POSITION""", e)
df.to_csv(OUT / "schema_columns.csv", index=False, encoding="utf-8-sig")
for t, g in df.groupby("t"):
    print(t, ", ".join(f"{r.c}:{r.d}" for r in g.itertuples()))
