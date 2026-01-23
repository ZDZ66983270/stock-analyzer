import sqlite3
import os

def list_tables(db_name):
    if not os.path.exists(db_name):
        print(f"{db_name} does not exist.")
        return

    print(f"--- Tables in {db_name} ---")
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        for t in tables:
            print(t[0])
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_tables('stock_data.db')
    list_tables('backend/database.db')
    list_tables('market_data.db')
