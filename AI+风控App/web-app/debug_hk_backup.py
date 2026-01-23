
import akshare as ak
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)

def test_hk_backup(symbol="00700"):
    print(f"Testing HK backup interface for {symbol}...\n")
    
    # stock_hk_fhpx_detail_ths
    print(f"--- stock_hk_fhpx_detail_ths(symbol='{symbol}') ---")
    try:
        # Note: symbol for this interface is typically 4 digits for HK? 
        # User example says "0700", let's try "0700" and "00700"
        
        test_code = symbol.lstrip('0')
        if len(test_code) < 4:
            test_code = test_code.zfill(4)
            
        print(f"Using code: {test_code}")
        
        df = ak.stock_hk_fhpx_detail_ths(symbol=test_code)
        if df is not None and not df.empty:
            print("Columns:", df.columns.tolist())
            print(df.head())
            
            # Check '方案' column for dividend amount info
            # Usually contains strings like "HKD 2.4000"
        else:
            print("No data returned.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_hk_backup("00700")
