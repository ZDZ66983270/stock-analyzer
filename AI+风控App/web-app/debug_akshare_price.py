import akshare as ak
import pandas as pd
from datetime import datetime

def check_stock(symbol, name):
    print(f"\nChecking {name} ({symbol})...")
    try:
        # 不复权
        df_raw = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date="20251201", end_date="20261231", adjust="")
        latest_raw = df_raw.iloc[-1]
        print(f"[不复权] Date: {latest_raw['日期']}, Close: {latest_raw['收盘']}")
        
        # 前复权
        df_qfq = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date="20251201", end_date="20261231", adjust="qfq")
        latest_qfq = df_qfq.iloc[-1]
        print(f"[前复权] Date: {latest_qfq['日期']}, Close: {latest_qfq['收盘']}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_stock("600030", "中信证券")
    check_stock("600519", "贵州茅台 (Reference)")
    check_stock("601519", "大智慧")
