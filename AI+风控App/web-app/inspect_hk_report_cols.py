import akshare as ak
import pandas as pd

pd.set_option('display.max_columns', None)

def inspect_hk_report():
    print("Fetching HK financial report (stock_financial_hk_report_em) for 00700...")
    try:
        # Check available report types (standard is usually summary, balance sheet, income, cashflow)
        # AkShare doc might specify 'indicator' arg or just returns a comprehensive table.
        # Let's try calling it without args first or with '年度' if supported.
        # Based on naming, it might return the main financial report indicators.
        
        # Let's guess args: symbol, indicator?
        df = ak.stock_financial_hk_report_em(symbol="00700", indicator="年度")
        
        if not df.empty:
            print("\n--- Columns ---")
            print(df.columns.tolist())
            print("\n--- First Row ---")
            print(df.iloc[0])
        else:
            print("Empty DataFrame returned.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_hk_report()
