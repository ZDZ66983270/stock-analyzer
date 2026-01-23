
import sqlite3
import pandas as pd
import os

def export_tsla():
    symbol = "US:STOCK:TSLA"
    db_path = "backend/database.db"
    output_dir = "exports"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    
    print(f"🔄 Exporting data for {symbol}...")
    
    try:
        # 1. Export Market Data
        market_query = f"""
        SELECT * FROM marketdatadaily 
        WHERE symbol = '{symbol}' 
        ORDER BY timestamp DESC
        """
        df_market = pd.read_sql_query(market_query, conn)
        market_file = os.path.join(output_dir, "TSLA_market_data.csv")
        df_market.to_csv(market_file, index=False)
        print(f"✅ Market Data exported: {market_file} ({len(df_market)} records)")
        
        # 2. Export Financial Data
        financial_query = f"""
        SELECT * FROM financialfundamentals
        WHERE symbol = '{symbol}' 
        ORDER BY as_of_date DESC
        """
        df_financial = pd.read_sql_query(financial_query, conn)
        financial_file = os.path.join(output_dir, "TSLA_financials.csv")
        df_financial.to_csv(financial_file, index=False)
        print(f"✅ Financial Data exported: {financial_file} ({len(df_financial)} records)")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    export_tsla()
