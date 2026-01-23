
import yfinance as yf
import pandas as pd

def inspect_yahoo():
    sym = "AAPL"
    print(f"Inspecting Yahoo for {sym}...")
    t = yf.Ticker(sym)
    
    try:
        inc = t.financials
        print("--- Income Statement Keys ---")
        print(inc.index.tolist())
        
        # Check specific rows
        for k in ['Net Income Common Stockholders', 'Diluted Average Shares', 'Basic Average Shares']:
            if k in inc.index:
                print(f"✅ Found {k}: {inc.loc[k].values[:2]}")
            else:
                print(f"❌ Missing {k}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_yahoo()
