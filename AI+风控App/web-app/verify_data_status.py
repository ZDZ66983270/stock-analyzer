
import sys
import os
import sqlite3
from datetime import datetime

# Adjust path to include backend
sys.path.append(os.path.join(os.getcwd(), 'backend'))

def verify_data():
    db_path = 'backend/database.db'
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Symbols to check
    symbols = ['600030.SH', '09988.HK', 'TSLA', 'MSFT', '00700.HK']
    
    print(f"{'Symbol':<10} {'Main DB Date':<20} {'Price':<10} {'Raw Fetch Time':<20} {'Raw Payload Date'}")
    print("-" * 100)
    
    for sym in symbols:
        # 1. Main DB (MarketDataDaily)
        # Handle case sensitivity logic if needed, but standard is usually upper
        # Try both upper and original
        cursor.execute("""
            SELECT date, close, updated_at 
            FROM marketdatadaily 
            WHERE symbol = ? OR symbol = ?
            ORDER BY date DESC LIMIT 1
        """, (sym, sym.upper()))
        
        main_row = cursor.fetchone()
        main_date = "N/A"
        price = "N/A"
        
        if main_row:
            main_date = main_row[0] # The 'date' field which we just patched
            price = f"{main_row[1]:.2f}"
            
        # 2. Raw Data (rawmarketdata)
        base_sym = sym.split('.')[0]
        cursor.execute("""
            SELECT fetch_time, payload 
            FROM rawmarketdata 
            WHERE symbol LIKE ? OR symbol LIKE ?
            ORDER BY fetch_time DESC LIMIT 1
        """, (f"%{sym}%", f"%{base_sym}%"))
        
        raw_row = cursor.fetchone()
        raw_fetch_time = "N/A"
        raw_payload_date = "N/A"
        
        if raw_row:
            raw_fetch_time = raw_row[0]
            # quick parse payload string to find time/date
            payload = raw_row[1]
            import json
            try:
                data = json.loads(payload)
                if isinstance(data, list) and len(data) > 0:
                    item = data[0]
                    raw_payload_date = item.get('date') or item.get('时间') or "N/A"
                elif isinstance(data, dict):
                    raw_payload_date = data.get('date') or data.get('时间') or "N/A"
            except:
                pass

        print(f"{sym:<10} {main_date:<20} {price:<10} {raw_fetch_time:<20} {raw_payload_date}")

    conn.close()

if __name__ == "__main__":
    verify_data()
