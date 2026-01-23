import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

print("--- RAW SQL Query MSFT.OQ Info ---")
cursor.execute("SELECT symbol, date, close, open, volume, dividend_yield FROM marketdata WHERE symbol='MSFT.OQ' AND period='1d'")
rows = cursor.fetchall()
for r in rows:
    print(r)

conn.close()
