
import akshare as ak
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)

def test_dividend_interfaces(symbol="600030"):
    print(f"Testing dividend interfaces for {symbol}...\n")
    
    # 1. stock_fhps_detail_em
    print(f"--- 1. stock_fhps_detail_em(symbol='{symbol}') ---")
    try:
        df_em = ak.stock_fhps_detail_em(symbol=symbol)
        if df_em is not None and not df_em.empty:
            print("Columns:", df_em.columns.tolist())
            
            # Check for Dividend Yield column
            target_col = '现金分红-股息率'
            if target_col in df_em.columns:
                print(f"\nFound column: '{target_col}'")
                # Sort by date (usually '报告期' or '最新公告日期')
                sort_col = '最新公告日期' if '最新公告日期' in df_em.columns else '详见说明'
                try:
                    df_em = df_em.sort_values(sort_col, ascending=False)
                except:
                    pass
                
                print("Recent 5 records:")
                print(df_em[[sort_col, '现金分红-现金分红比例', target_col]].head(5))
            else:
                print(f"Column '{target_col}' NOT found.")
        else:
            print("No data returned.")
    except Exception as e:
        print(f"Error: {e}")
        
    print("\n" + "="*50 + "\n")

    # 2. stock_fhps_detail_ths
    print(f"--- 2. stock_fhps_detail_ths(symbol='{symbol}') ---")
    try:
        df_ths = ak.stock_fhps_detail_ths(symbol=symbol)
        if df_ths is not None and not df_ths.empty:
            print("Columns:", df_ths.columns.tolist())
             # Check for Yield related columns
            yield_cols = [c for c in df_ths.columns if '率' in c]
            print("Yield related columns:", yield_cols)
            
            print("Recent 5 records:")
            print(df_ths.head(5))
        else:
            print("No data returned.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_dividend_interfaces("600030")
