
import sys
import os
import pandas as pd
sys.path.append('backend')
from fetch_valuation_history import fetch_cn_dividend_yield

def test_cn_div():
    print("Testing CN Dividend Yield Fetching...")
    
    # 600519: Kweichow Moutai (Usually pays)
    # 601398: ICBC (Usually pays)
    # 002594: BYD (Small yield)
    
    symbols = ['CN:STOCK:600519', 'CN:STOCK:601398', 'CN:STOCK:002594']
    
    for s in symbols:
        print(f"\n🔍 Checking {s}...")
        try:
            yield_val = fetch_cn_dividend_yield(s)
            print(f"   👉 Yield: {yield_val}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_cn_div()
