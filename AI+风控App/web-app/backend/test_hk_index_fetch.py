import akshare as ak
import pandas as pd

print("Testing HK Index Interfaces...")

# 1. Try stock_hk_index_daily_sina (Common for HSI)
# Symbols: HSI, HSCEI, HSTECH?
try:
    print("\n[Test 1] stock_hk_index_daily_sina (symbol='HSI')...")
    df = ak.stock_hk_index_daily_sina(symbol="HSI")
    print(f"Success! Shape: {df.shape}")
    print(df.tail(3))
except Exception as e:
    print(f"Failed: {e}")

try:
    print("\n[Test 2] stock_hk_index_daily_sina (symbol='HSTECH')...")
    df = ak.stock_hk_index_daily_sina(symbol="HSTECH") # Guessing symbol
    print(f"Success! Shape: {df.shape}")
except Exception as e:
    print(f"Failed: {e}")

# 2. Try stock_hk_daily (EastMoney) with '800000' (Index code in EM)
try:
    print("\n[Test 3] stock_hk_daily (symbol='800000')...")
    df = ak.stock_hk_daily(symbol="800000", adjust="qfq")
    print(f"Success! Shape: {df.shape}")
except Exception as e:
    print(f"Failed: {e}")

# 3. Try stock_hk_index_spot_em (To check codes)
try:
    print("\n[Test 4] stock_hk_index_spot_em (To find codes)...")
    df = ak.stock_hk_index_spot_em()
    print(df[df['名称'].str.contains('恒生')])
except Exception as e:
    print(f"Failed: {e}")
