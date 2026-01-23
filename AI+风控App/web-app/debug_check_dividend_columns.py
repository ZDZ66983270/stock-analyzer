
import akshare as ak
import pandas as pd

def check_columns():
    print("Checking columns of stock_fhps_detail_em for 600030...")
    try:
        df = ak.stock_fhps_detail_em(symbol="600030")
        if df is not None:
            print("Columns:", df.columns.tolist())
            print("First row:", df.iloc[0].to_dict())
            
            # Look for relevant columns
            print("\nRecent 5 records:")
            # Sort by date
            if '公告日期' in df.columns:
                df = df.sort_values('公告日期', ascending=False)
            elif '最新公告日期' in df.columns:
                 df = df.sort_values('最新公告日期', ascending=False)
                 
            print(df.head()[['报告期', '每股股利(税前)', '每股红股', '除权除息日', '股权登记日']])
            
    except Exception as e:
        print(f"Error: {e}")
        # Try stock_history_dividend_detail as fallback
        print("\nChecking stock_history_dividend_detail...")
        try:
            df2 = ak.stock_history_dividend_detail(symbol="600030", date="")
            print("Columns:", df2.columns.tolist())
            print(df2.head())
        except Exception as e2:
             print(f"Error 2: {e2}")

if __name__ == "__main__":
    check_columns()
