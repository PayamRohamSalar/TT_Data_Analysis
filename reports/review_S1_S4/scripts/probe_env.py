import sys
import os

print(f"Python: {sys.executable}")
print(f"Version: {sys.version}")

try:
    import pandas as pd
    print(f"pandas: {pd.__version__}")
except Exception as e:
    print(f"pandas error: {e}")

try:
    import sqlalchemy
    print(f"sqlalchemy: {sqlalchemy.__version__}")
except Exception as e:
    print(f"sqlalchemy error: {e}")

try:
    from tt_bank.db.connection import get_engine
    engine = get_engine()
    with engine.connect() as conn:
        res = conn.execute(sqlalchemy.text("SELECT @@VERSION AS ver, DB_NAME() AS db")).fetchone()
        print(f"DB connected: db={res[1]}, ver={res[0][:40]}")
except Exception as e:
    print(f"DB connection error: {e}")
