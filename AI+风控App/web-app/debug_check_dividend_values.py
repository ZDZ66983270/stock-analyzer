
import akshare as ak
import pandas as pd

def check_dividend_values():
    print("Checking values of stock_history_dividend_detail for 600030...")
    try:
        # Fetch data
        df = ak.stock_history_dividend_detail(symbol="600030", date="")
        if df is not None:
            # Filter for recent records
            df['除权除息日'] = pd.to_datetime(df['除权除息日'])
            recent_df = df[df['除权除息日'] > '2023-01-01'].sort_values('除权除息日', ascending=False)
            
            print("Recent Dividend Records:")
            print(recent_df[['公告日期', '除权除息日', '派息']])
            
            # Also check Price source
            info = ak.stock_individual_info_em(symbol="600030")
            price_row = info[info['item'] == '最新']
            print("\nCurrent Price Info:")
            print(price_row)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_dividend_values()
