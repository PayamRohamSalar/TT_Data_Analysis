import time
from sqlalchemy import text
from tt_bank.db.connection import get_engine
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

t0 = time.time()
engine = get_engine()

print("Connected. Running count...")
with engine.connect() as conn:
    row_count = conn.execute(text("SELECT COUNT(*) FROM dbo.Loan_Remain")).scalar()
    print(f"Loan_Remain row count: {row_count:,} ({time.time()-t0:.1f}s)")
