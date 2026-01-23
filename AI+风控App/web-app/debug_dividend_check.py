
import yfinance as yf
import akshare as ak
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("DividendCheck")

def check_yfinance_units():
    print("\n" + "="*50)
    print("🔍 Checking yfinance Dividend Yield Units (US & HK)")
    print("="*50)
    
    # Test cases: US (Apple), HK (Tencent)
    symbols = [
        ('US', 'AAPL', 'AAPL'),
        ('HK', '0700.HK', '00700')
    ]
    
    for market, yf_symbol, code in symbols:
        try:
            print(f"\n--- Testing {market}: {yf_symbol} ---")
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info
            
            # Key fields to check
            div_yield = info.get('dividendYield')
            div_rate = info.get('dividendRate')
            
            print(f"Raw 'dividendYield': {div_yield}")
            print(f"Raw 'dividendRate':  {div_rate}")
            
            if div_yield:
                print(f"Interpretation:")
                print(f"  As Percentage: {div_yield}%  (e.g., 0.005 -> 0.005%)")
                print(f"  As Decimal:    {div_yield*100:.2f}% (e.g., 0.005 -> 0.50%)")
                
        except Exception as e:
            print(f"Error fetching {yf_symbol}: {e}")

def check_akshare_ashare():
    print("\n" + "="*50)
    print("🔍 Checking AkShare A-Share Dividend Availability")
    print("="*50)
    
    code = "600030" # CITIC Securities
    
    # 1. Spot Data (Real-time)
    try:
        print(f"\n1. Testing ak.stock_zh_a_spot_em() for {code}...")
        df_spot = ak.stock_zh_a_spot_em()
        # Filter for our stock
        row = df_spot[df_spot['代码'] == code]
        if not row.empty:
            print("Columns found containing '股息' or '率':")
            cols = [c for c in row.columns if '股息' in c or '率' in c]
            print(row[cols].to_string(index=False))
        else:
            print("Stock not found in spot data.")
            
    except Exception as e:
        print(f"Spot API Error: {e}")

    # 2. Individual Info (Basic Info)
    try:
        print(f"\n2. Testing ak.stock_individual_info_em(symbol='{code}')...")
        df_info = ak.stock_individual_info_em(symbol=code)
        # Check if any row has '股息'
        div_rows = df_info[df_info['item'].str.contains('股息', na=False)]
        if not div_rows.empty:
            print("Found dividend info:")
            print(div_rows)
        else:
            print("No '股息' item found in individual info.")
            
    except Exception as e:
        print(f"Info API Error: {e}")

    # 3. LG Indicator (Historical Valuation) - THIS IS THE OFFICIAL VALUATION INTERFACE
    try:
        print(f"\n3. Testing ak.stock_a_indicator_lg(symbol='{code}')...")
        df_lg = ak.stock_a_indicator_lg(symbol=code)
        if df_lg is not None and not df_lg.empty:
            print("Columns:", df_lg.columns.tolist())
            latest = df_lg.iloc[-1]
            print(f"Latest Record ({latest['trade_date']}):")
            # dv_ratio is usually dividend yield
            if 'dv_ratio' in latest:
                print(f"  dv_ratio: {latest['dv_ratio']} (Likely Dividend Yield)")
            if 'dv_ttm' in latest:
                print(f"  dv_ttm:   {latest['dv_ttm']} (Likely TTM Yield)")
        else:
            print("No data returned.")
            
    except Exception as e:
        print(f"LG Indicator API Error: {e}")

if __name__ == "__main__":
    check_yfinance_units()
    check_akshare_ashare()
