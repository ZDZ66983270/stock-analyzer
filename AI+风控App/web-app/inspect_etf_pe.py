import sqlite3
import pandas as pd
import os

def check_etf_pe():
    db_path = 'backend/database.db'
    if not os.path.exists(db_path):
        print(f"{db_path} does not exist.")
        return

    conn = sqlite3.connect(db_path)
    
    # 1. Check Watchlist for ETFs using SYMBOL pattern
    print("--- Searching for ETFs in Watchlist (symbol pattern '%:ETF:%') ---")
    try:
        # Note: 'symbol' column holds the canonical ID like 'CN:ETF:123456'
        query_etfs = "SELECT id, symbol, name FROM watchlist WHERE symbol LIKE '%:ETF:%' OR symbol LIKE '%:Fund:%'"
        etfs = pd.read_sql_query(query_etfs, conn)
        print(f"Found {len(etfs)} ETFs.")
        
        if not etfs.empty:
            print("Sample ETFs:")
            print(etfs.head())
    except Exception as e:
        print(f"Error reading Watchlist: {e}")
        conn.close()
        return

    if etfs.empty:
        print("No ETFs found.")
        conn.close()
        return

    # 2. Check MarketDataDaily for PE/PE TTM
    # filtering by symbol
    etf_symbols = etfs['symbol'].tolist()
    sym_placeholder = ','.join(['?'] * len(etf_symbols))
    
    print("\n--- Checking Valuation Data Coverage ---")
    
    try:
        # Check coverage count
        query_coverage = f"""
            SELECT 
                symbol,
                COUNT(pe) as pe_count,
                COUNT(pe_ttm) as pe_ttm_count,
                MAX(timestamp) as last_date
            FROM marketdatadaily 
            WHERE symbol IN ({sym_placeholder})
            GROUP BY symbol
            HAVING pe_count > 0 OR pe_ttm_count > 0
        """
        
        if len(etf_symbols) > 900:
            print(f"Too many ETFs ({len(etf_symbols)}), checking first 900 for overview.")
            batch_syms = etf_symbols[:900]
            batch_placeholder = ','.join(['?'] * len(batch_syms))
            query_coverage = query_coverage.replace(sym_placeholder, batch_placeholder)
            coverage = pd.read_sql_query(query_coverage, conn, params=batch_syms)
        else:
            coverage = pd.read_sql_query(query_coverage, conn, params=etf_symbols)
            
        print(f"\nETFs with ANY valuation data: {len(coverage)}")
        
        if not coverage.empty:
            print(coverage.head())
            print("\nStats:")
            print(f"Total ETFs checked: {len(etf_symbols)}")
            print(f"ETFs with PE data: {len(coverage[coverage['pe_count'] > 0])}")
            print(f"ETFs with PE TTM data: {len(coverage[coverage['pe_ttm_count'] > 0])}")
            
            # Detailed sample check
            print("\nLatest values for up to 5 ETFs with data:")
            sample_syms = coverage['symbol'].head(5).tolist()
            for sym in sample_syms:
                q = "SELECT timestamp, pe, pe_ttm FROM marketdatadaily WHERE symbol = ? ORDER BY timestamp DESC LIMIT 3"
                r = pd.read_sql_query(q, conn, params=(sym,))
                print(f"\nAsset: {sym}")
                print(r)
        else:
            print("No PE/PE TTM data found for ANY of the checked ETFs.")

    except Exception as e:
        print(f"Error checking coverage: {e}")
        
    conn.close()

if __name__ == "__main__":
    check_etf_pe()
