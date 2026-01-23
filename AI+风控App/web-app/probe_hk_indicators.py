import akshare as ak
import pandas as pd

def probe_hk_indicators():
    symbol = "00700"
    indicators = ["资产负债表", "利润表", "现金流量表", "业绩公报"]
    
    print(f"Probing {symbol} with stock_financial_hk_report_em...")
    
    for ind in indicators:
        print(f"\n--- Indicator: {ind} ---")
        try:
            df = ak.stock_financial_hk_report_em(symbol=symbol, indicator=ind)
            if not df.empty:
                print(f"✅ Found {len(df)} rows.")
                print(f"Columns: {df.columns.tolist()[:10]}...") # Print first 10 cols
            else:
                print("❌ Empty.")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    probe_hk_indicators()
