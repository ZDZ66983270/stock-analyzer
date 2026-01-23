import sqlite3

def enable_wal():
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        mode = cursor.fetchone()
        print(f"Journal Mode set to: {mode[0]}")
        conn.close()
    except Exception as e:
        print(f"Failed to enable WAL: {e}")

if __name__ == "__main__":
    enable_wal()
