import sqlite3
import pandas as pd

db_path = "vera.db"
conn = sqlite3.connect(db_path)
query = "SELECT valuation_status, COUNT(*) as count FROM analysis_snapshot GROUP BY valuation_status;"
df = pd.read_sql_query(query, conn)
print("Valuation Status Distribution:")
print(df)

query2 = "SELECT asset_id, valuation_status, created_at FROM analysis_snapshot ORDER BY created_at DESC LIMIT 10;"
df2 = pd.read_sql_query(query2, conn)
print("\nLatest 10 records:")
print(df2.to_string())
conn.close()
