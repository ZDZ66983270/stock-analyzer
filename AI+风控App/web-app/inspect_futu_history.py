
import sys
import logging
from futu import *

# Mock logging behavior if needed or just print
logging.basicConfig(level=logging.INFO)

def inspect_futu():
    try:
        ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
        
        # 1. 尝试获取历史 K 线，看包含哪些列
        print("Checking History K-Line columns...")
        ret, data, page_req_key = ctx.request_history_kline(
            'HK.00700', 
            start='2025-01-01', 
            end='2026-01-01', 
            max_count=5
        )
        if ret == RET_OK:
            print("K-Line Columns:", data.columns.tolist())
            print("Sample Data:\n", data.head(1))
        else:
            print("Failed to fetch K-Line:", data)

        # 2. 检查是否有相关API
        print("\nChecking available methods in OpenQuoteContext...")
        methods = [m for m in dir(ctx) if 'financial' in m or 'valuation' in m or 'ratio' in m]
        print("Potential methods:", methods)
        
        ctx.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_futu()
