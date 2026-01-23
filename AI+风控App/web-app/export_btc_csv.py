
import sqlite3
import pandas as pd
import os

def export_btc_to_csv():
    db_path = os.path.join(os.getcwd(), 'backend', 'database.db')
    export_dir = os.path.join(os.getcwd(), 'backend', 'exports')
    os.makedirs(export_dir, exist_ok=True)
    
    csv_path = os.path.join(export_dir, 'btc_history_10y.csv')
    
    print(f"📂 Connecting to database at {db_path}...")
    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT * FROM marketdatadaily 
    WHERE symbol = 'BTC-USD' 
    ORDER BY timestamp ASC
    """
    
    print("📊 Querying BTC history...")
    df = pd.read_sql_query(query, conn)
    
    if df.empty:
        print("⚠️ No BTC data found in database.")
    else:
        print(f"✅ Exporting {len(df)} rows to {csv_path}...")
        df.to_csv(csv_path, index=False)
        print("🎉 Export complete.")
    
    conn.close()

if __name__ == "__main__":
    export_btc_to_csv()
