import sqlite3
import pandas as pd
import os

# Connect to DB
db_path = "database.db"
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)

# Ensure export dir
export_dir = "exports"
os.makedirs(export_dir, exist_ok=True)

# Get all tables
tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)

print(f"Found tables: {tables['name'].tolist()}")

for table_name in tables['name']:
    print(f"Exporting {table_name}...")
    try:
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
        csv_path = os.path.join(export_dir, f"{table_name}.csv")
        df.to_csv(csv_path, index=False)
        print(f"Saved {csv_path} ({len(df)} rows)")
    except Exception as e:
        print(f"Failed to export {table_name}: {e}")

conn.close()
print("\nExport Complete! Check 'web-app/backend/exports/' directory.")
