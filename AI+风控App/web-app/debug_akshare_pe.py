
import akshare as ak
import pandas as pd

def test_cn_pe(symbol):
    code = symbol.split(".")[0]
    print(f"Testing AkShare PE for {code}...")
    try:
        df = ak.stock_a_indicator_lg(symbol=code)
        if df.empty:
            print("❌ Empty DataFrame")
        else:
            print(f"✅ Fetched {len(df)} rows")
            print(df.head())
            print(df.columns)
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_cn_pe("600309.SH")
