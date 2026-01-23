import akshare as ak
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)

def test_cn_etf_valuation():
    # Example ETFs: 
    # 510050 (SSE 50 ETF)
    # 159915 (ChiNext ETF)
    # 159919 (CSI 300 ETF - maybe) -> 510300 is CSI 300 ETF
    
    etfs = ['510050', '159915'] 
    
    print("--- Testing stock_value_em for ETFs ---")
    for code in etfs:
        try:
            print(f"Fetching {code}...")
            df = ak.stock_value_em(symbol=code)
            if df is None or df.empty:
                print(f"❌ {code}: No data or empty")
            else:
                print(f"✅ {code}: Got {len(df)} rows")
                print(df.head(2))
        except Exception as e:
            print(f"❌ {code}: Error - {e}")

if __name__ == "__main__":
    test_cn_etf_valuation()
