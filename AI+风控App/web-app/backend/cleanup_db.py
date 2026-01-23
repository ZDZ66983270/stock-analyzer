import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

print("--- Cleaning up Bad US Records (Raw SQL) ---")
symbols = ["MSFT.OQ", "TSM.N", "GOOG.OQ", "106.NVDA", "09988.hk", "00998.hk", "00700.hk", "01919.hk"]

for sym in symbols:
    cursor.execute("DELETE FROM marketdata WHERE symbol=? AND period='1d'", (sym,))
    print(f"Deleted records for {sym}: {cursor.rowcount}")

conn.commit()
conn.close()
print("Cleanup Complete.")
