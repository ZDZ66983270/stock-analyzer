
import sys
import os
import sqlite3

def check_watchlist():
    db_path = 'backend/database.db'
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Checking Watchlist Table:")
    cursor.execute("SELECT * FROM watchlist")
    rows = cursor.fetchall()
    if not rows:
        print("Watchlist is EMPTY")
    else:
        for row in rows:
            print(row)
            
    conn.close()

if __name__ == "__main__":
    check_watchlist()
