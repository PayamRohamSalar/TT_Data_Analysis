import sqlalchemy
from tt_bank.db.connection import get_engine

try:
    engine = get_engine()
    with engine.connect() as conn:
        res = conn.execute(sqlalchemy.text("SELECT @@SERVERNAME, DB_NAME(), GETDATE()")).fetchone()
        print("Connected successfully:", res)
except Exception as e:
    print("Connection failed:", e)
