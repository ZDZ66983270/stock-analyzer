
import sys
import os
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Database Path
DB_PATH = os.path.join(os.path.dirname(__file__), 'backend/database.db')
DATABASE_URL = f"sqlite:///{DB_PATH}"

def check_db_status():
    print(f"Checking Database: {DB_PATH}")
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # 1. Get all assets from Watchlist
        # Note: Watchlist doesn't have 'type', we infer it from symbol (e.g. CN:STOCK:123)
        query_assets = text("""
            SELECT id, symbol, name, market 
            FROM watchlist 
            ORDER BY market, symbol
        """)
        assets_df = pd.read_sql(query_assets, conn)
        
        if assets_df.empty:
            print("Watchlist is empty.")
            return

        # Infer Type
        def get_type(sym):
            parts = sym.split(':')
            if len(parts) >= 3:
                return parts[1] # [MARKET, TYPE, CODE]
            return "UNKNOWN"
            
        assets_df['type'] = assets_df['symbol'].apply(get_type)

        print(f"\nTotal Assets: {len(assets_df)}")
        
        # 2. Get Statistics from MarketDataDaily
        print("Analyzing Market Data History & Valuation...")
        
        stats_query = text("""
            WITH LatestDaily AS (
                SELECT 
                    symbol,
                    close,
                    timestamp,
                    pe,
                    pb,
                    dividend_yield,
                    ROW_NUMBER() OVER(PARTITION BY symbol ORDER BY timestamp DESC) as rn
                FROM marketdatadaily
            ),
            HistoryStats AS (
                SELECT 
                    symbol,
                    COUNT(*) as days_count,
                    COUNT(pe) as pe_count,
                    COUNT(pb) as pb_count,
                    MIN(timestamp) as first_date,
                    MAX(timestamp) as last_date
                FROM marketdatadaily
                GROUP BY symbol
            )
            SELECT 
                w.symbol,
                h.days_count,
                h.pe_count,
                h.pb_count,
                h.first_date,
                h.last_date,
                l.close as latest_close,
                l.pe as latest_pe,
                l.pb as latest_pb,
                l.dividend_yield as latest_yield
            FROM watchlist w
            LEFT JOIN HistoryStats h ON w.symbol = h.symbol
            LEFT JOIN LatestDaily l ON w.symbol = l.symbol AND l.rn = 1
        """)
        
        stats_df = pd.read_sql(stats_query, conn)
        
        # 3. Get Financial Report Stats (Annual/Quarterly)
        print("Analyzing Financial Reports...")
        fin_query = text("""
            SELECT 
                symbol,
                report_type,
                COUNT(*) as count,
                MIN(as_of_date) as start_date,
                MAX(as_of_date) as end_date
            FROM financialfundamentals
            GROUP BY symbol, report_type
        """)
        fin_df = pd.read_sql(fin_query, conn)
        
        # Merge Daily stats first
        df = pd.merge(assets_df, stats_df, on='symbol', how='left')
        
        # Format dates
        df['first_date'] = pd.to_datetime(df['first_date'], errors='coerce').dt.date
        df['last_date'] = pd.to_datetime(df['last_date'], errors='coerce').dt.date
        
        # Calculate Coverage
        df['pe_cover'] = (df['pe_count'] / df['days_count'] * 100).fillna(0).round(0).astype(int)
        df['pb_cover'] = (df['pb_count'] / df['days_count'] * 100).fillna(0).round(0).astype(int)
        
        # Process Financial Stats
        fin_info = {} # symbol -> {annual: "str", quarterly: "str"}
        if not fin_df.empty:
            for _, row in fin_df.iterrows():
                sym = row['symbol']
                rtype = row['report_type']
                count = row['count']
                start = str(row['start_date'])[:4] # Year only
                end = str(row['end_date'])[:4]
                
                info_str = f"{start}-{end}({count})"
                
                if sym not in fin_info: fin_info[sym] = {'annual': '-', 'quarterly': '-'}
                fin_info[sym][rtype] = info_str
        
        # Sort key
        df = df.sort_values(by=['market', 'type', 'symbol'])
        
        # Consolidate into a single table
        print("\n=== Market Data & Valuation Status (估值回填检查) ===")
        # Header
        header = f"{'Symbol':<18} {'Date':<12} {'Close':<8} {'PE(Last)':<9} {'PE Cover':<9} {'PB(Last)':<9} {'PB Cover':<9} {'Yield':<8}"
        print(header)
        print("-" * len(header))
        
        for _, row in df.iterrows():
            # Basic info
            ts = str(row['last_date']) if pd.notna(row['last_date']) else "-"
            close = f"{row['latest_close']:.2f}" if pd.notna(row['latest_close']) else "-"
            
            # PE Info
            pe = f"{row['latest_pe']:.2f}" if pd.notna(row['latest_pe']) else "-"
            pe_cov = f"{row['pe_cover']}%"
            
            # PB Info
            pb = f"{row['latest_pb']:.2f}" if pd.notna(row['latest_pb']) else "-"
            pb_cov = f"{row['pb_cover']}%"
            
            # Yield
            dy = f"{row['latest_yield']:.2f}%" if pd.notna(row['latest_yield']) else "-"
            
            print(f"{row['symbol']:<18} {ts:<12} {close:<8} {pe:<9} {pe_cov:<9} {pb:<9} {pb_cov:<9} {dy:<8}")
            
        print("-" * len(header))
        print(f"Total Assets: {len(df)}")
        print("Note: 'PE Cover' = (Days with PE / Total Days) * 100%. 100% means fully filled.")

if __name__ == "__main__":
    check_db_status()
