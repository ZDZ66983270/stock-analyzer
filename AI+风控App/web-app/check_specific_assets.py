
import sys
import os
import pandas as pd
from sqlalchemy import create_engine, text

# Database Path
DB_PATH = os.path.join(os.path.dirname(__file__), 'backend/database.db')
DATABASE_URL = f"sqlite:///{DB_PATH}"

def check_assets():
    engine = create_engine(DATABASE_URL)
    targets = ['03427', '0P00014FO3']
    
    print(f"Checking assets: {targets}")
    
    with engine.connect() as conn:
        for t in targets:
            print(f"\n{'='*60}")
            print(f"🔍 Analyzing: {t}")
            print(f"{'='*60}")
            
            # 1. Watchlist
            query_w = text("SELECT * FROM watchlist WHERE symbol LIKE :s")
            df_w = pd.read_sql(query_w, conn, params={"s": f"%{t}%"})
            if df_w.empty:
                print("❌ Watchlist: Not Found")
            else:
                print("✅ Watchlist:")
                print(df_w.to_string(index=False))
                
                # Get exact symbol for next queries
                symbol = df_w.iloc[0]['symbol']
                market = df_w.iloc[0]['market']
                
                # 2. MarketDataDaily
                query_d = text("""
                    SELECT count(*) as count, min(timestamp) as min_ts, max(timestamp) as max_ts, 
                           avg(close) as avg_price
                    FROM marketdatadaily 
                    WHERE symbol = :sym
                """)
                df_d = pd.read_sql(query_d, conn, params={"sym": symbol})
                print(f"\n📊 MarketDataDaily: {df_d.iloc[0]['count']} records")
                if df_d.iloc[0]['count'] > 0:
                     print(f"   Range: {df_d.iloc[0]['min_ts']} -> {df_d.iloc[0]['max_ts']}")
                     
                     # Show last 5 records
                     query_d5 = text("SELECT * FROM marketdatadaily WHERE symbol = :sym ORDER BY timestamp DESC LIMIT 5")
                     df_d5 = pd.read_sql(query_d5, conn, params={"sym": symbol})
                     print("   Latest 5 records:")
                     print(df_d5[['timestamp', 'open', 'high', 'low', 'close', 'volume']].to_string(index=False))

                # 3. MarketSnapshot
                query_s = text("SELECT * FROM marketsnapshot WHERE symbol = :sym")
                df_s = pd.read_sql(query_s, conn, params={"sym": symbol})
                print(f"\n📸 MarketSnapshot:")
                if df_s.empty:
                    print("   ❌ Not Found")
                else:
                    print(df_s[['timestamp', 'price', 'pe', 'pb', 'dividend_yield', 'updated_at']].to_string(index=False))

if __name__ == "__main__":
    check_assets()
