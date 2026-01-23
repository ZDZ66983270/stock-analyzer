
import akshare as ak
import pandas as pd

def check_abstract_indicators():
    print("Checking indicators in stock_financial_abstract for 600030...")
    try:
        df = ak.stock_financial_abstract(symbol="600030")
        if df is not None:
             indicators = df['指标'].unique().tolist()
             print("All Indicators:", indicators)
             
             div_related = [i for i in indicators if '股利' in i or '股息' in i or '分红' in i]
             print("\nDividend Related Indicators:", div_related)
             
             if div_related:
                 # Print the data for these
                 print(df[df['指标'].isin(div_related)].iloc[:, :5]) # Print first few columns

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_abstract_indicators()
