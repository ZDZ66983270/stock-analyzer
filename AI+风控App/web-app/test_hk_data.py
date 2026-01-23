import yfinance as yf
import akshare as ak

def check_hk_yahoo(symbol):
    print(f"Checking Yahoo for {symbol}...")
    try:
        ticker = yf.Ticker(symbol)
        fin = ticker.financials
        if not fin.empty:
            print(f"Yahoo Columns (Dates): {len(fin.columns)}")
            print(fin.columns)
        else:
            print("Yahoo: Empty financials")
    except Exception as e:
        print(f"Yahoo Error: {e}")

def check_hk_akshare(symbol_code):
    print(f"Checking AkShare for {symbol_code}...")
    try:
        # Tried to find a dedicated HK financial interface.
        # Common one: stock_hk_financials (EastMoney) or similar
        print("Searching for HK financials interfaces...")
        # Note: stock_financial_hk_analysis_indicator_em might exist
        try:
             df = ak.stock_financial_hk_analysis_indicator_em(symbol=symbol_code, indicator="年度")
             if df is not None and not df.empty:
                 print(f"AkShare Found {len(df)} records")
                 print(df.head())
             else:
                 print("AkShare: Empty return")
        except Exception as e:
            print(f"AkShare Try 1 Error: {e}")
            
    except Exception as e:
        print(f"AkShare Error: {e}")

print("--- Validating HK Data ---")
check_hk_yahoo("0700.HK")
check_hk_akshare("00700")
