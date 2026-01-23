import akshare as ak
import os
import pandas as pd

# Simulate DataFetcher environment
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
no_proxy_domains = ["eastmoney.com", "push2his.eastmoney.com", "quote.eastmoney.com"]
os.environ["no_proxy"] = ",".join(no_proxy_domains)

print("Testing AkShare fetch for 600519...")
try:
    df = ak.stock_zh_a_hist_min_em(symbol="600519", period="1")
    print(f"Result Type: {type(df)}")
    if df is not None:
        print(f"Result Shape: {df.shape}")
        if not df is empty:
            print(df.tail(2))
        else:
            print("Result is Empty")
    else:
        print("Result is None")
except Exception as e:
    print(f"Fetch Failed: {e}")
