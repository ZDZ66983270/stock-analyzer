import akshare as ak
import pandas as pd
import os

def load_symbols():
    symbols = []
    path = 'imports/symbols.txt'
    if os.path.exists(path):
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'): continue
                if line.isdigit() and len(line) == 6: # Simple filter for CN/HK codes
                    symbols.append(line)
    return symbols

def check_cn_symbol_interface():
    symbols = load_symbols()
    print(f"Loaded symbols: {symbols}")
    
    # Filter for likely CN symbols (6 digits, often start with 6/0/3)
    # Just take first valid one
    target = None
    for s in symbols:
        if s.startswith('6') or s.startswith('0') or s.startswith('3'):
            target = s
            break
            
    if not target:
        target = "600030" # Fallback
        
    print(f"--- Checking AkShare CN Per-Symbol for {target} ---")
    
    # 1. Financial Abstract (同花顺)
    try:
        print("\n1. Trying stock_financial_abstract(symbol=...) [THS]")
        df = ak.stock_financial_abstract(symbol=target)
        if df is not None and not df.empty:
            print(f"✅ Success! Columns: {df.columns.tolist()[:5]} ...")
            print(df.head(2))
        else:
            print("   ❌ Returned empty.")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # 2. Financial Report Sina (新浪)
    try:
        print("\n2. Trying stock_financial_report_sina(symbol=...) [Sina]")
        df = ak.stock_financial_report_sina(stock=target, symbol="现金流量表")
        if df is not None and not df.empty:
            print(f"✅ Success! Columns: {df.columns.tolist()[:5]} ...")
        else:
            print("   ❌ Returned empty.")
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    check_cn_symbol_interface()
