import akshare as ak
import pandas as pd

def check_stock(code):
    print(f"--- Checking {code} (Cash Flow) ---")
    try:
        df = ak.stock_financial_hk_report_em(stock=code, symbol="现金流量表", indicator="年度")
        if df is None or df.empty:
            print("Empty DataFrame")
            return
        
        # Filter 
        print(f"Total rows: {len(df)}")
        print(df[df['STD_ITEM_NAME'].isin(['已付股息(融资)', '已付股息', '支付股利、利润或偿付利息支付的现金'])].head(10))
    except Exception as e:
        print(f"Error: {e}")

check_stock("03968")
check_stock("00998")
