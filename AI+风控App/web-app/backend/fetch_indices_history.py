import csv
import os
import akshare as ak
import pandas as pd
import time
from datetime import datetime

# Path Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LIBRARY_DIR = os.path.join(BASE_DIR, 'market_data_library')
INDICES_CSV = os.path.join(LIBRARY_DIR, 'global_indices.csv')

def fetch_history(symbol, market, name):
    print(f"Fetching history for {name} ({symbol})...")
    df = pd.DataFrame()
    
    try:
        # --- US Market ---
        if market == 'US':
            # Mapping common names to AkShare/Sina codes if needed
            # DJI -> .DJI, etc. But using ak.stock_us_daily might need specific format.
            # Using yfinance/Sina fallback logic or AkShare direct.
            # AkShare 'stock_us_daily' takes symbols like 'AAPL', 'AMZN' or '.DJI'?
            # Let's try EastMoney/Sina interface usually.
            # For Indices: .DJI, .IXIC, .INX usually.
            
            target_sym = symbol
            if symbol == 'DJI': target_sym = '.DJI'
            elif symbol == 'NDX': target_sym = '.NDX' # or .IXIC
            elif symbol == 'SPY': target_sym = 'SPY' # ETF
            
            # Using stock_us_daily (Sina)
            try:
                df = ak.stock_us_daily(symbol=target_sym, adjust="qfq")
            except:
                print(f"AkShare failed for {symbol}, trying simplified...")
        
        # --- HK Market ---
        elif market == 'HK':
            # Mapping specific numeric codes to Sina Index Symbols
            hk_map = {
                '800000': 'HSI',       # Hang Seng Index
                '800700': 'HSTECH',    # Hang Seng Tech
                'HSI': 'HSI',
                'HSTECH': 'HSTECH'
            }
            
            sina_symbol = hk_map.get(symbol, symbol)
            
            try:
                # Use Sina Index Interface (verified working)
                df = ak.stock_hk_index_daily_sina(symbol=sina_symbol)
            except Exception as e:
                print(f"  [!] Sina Index failed for {symbol}: {e}")
                # Fallback to stock interface? Unlikely to work for indices.
                df = pd.DataFrame()
            
        # --- CN Market ---
        elif market == 'CN':
            # 000001.SS -> sh000001
            code = symbol.split('.')[0]
            prefix = 'sh' if symbol.endswith('SS') or symbol.startswith('6') else 'sz'
            try:
                # Try Index Interface first for 000001
                if code == '000001':
                    df = ak.stock_zh_index_daily(symbol="sh000001")
                else:
                    df = ak.stock_zh_a_daily(symbol=f"{prefix}{code}", adjust="qfq")
            except:
                # Retry generic
                df = ak.stock_zh_a_daily(symbol=f"{prefix}{code}", adjust="qfq")

        if df is None or df.empty:
            print(f"  [X] No data found for {symbol}")
            return False

        # Save
        filename = f"history_{symbol}.csv"
        save_path = os.path.join(LIBRARY_DIR, filename)
        df.to_csv(save_path, index=False)
        print(f"  [V] Saved to {filename} ({len(df)} rows)")
        return True

    except Exception as e:
        print(f"  [!] Error: {e}")
        return False

def main():
    if not os.path.exists(INDICES_CSV):
        print("Indices CSV not found.")
        return

    # Load targets
    targets = []
    with open(INDICES_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            targets.append(row)

    print(f"Found {len(targets)} indices to download.")
    
    for t in targets:
        fetch_history(t['symbol'], t['market'], t['name'])
        time.sleep(2) # Polite delay

if __name__ == "__main__":
    main()
