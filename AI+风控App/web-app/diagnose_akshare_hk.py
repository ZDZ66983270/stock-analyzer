
import akshare as ak
import pandas as pd

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

def diagnose(symbol):
    print(f"--- Diagnosing {symbol} ---")
    try:
        df = ak.stock_financial_hk_analysis_indicator_em(symbol=symbol, indicator="报告期")
        if df.empty:
            print("Empty DataFrame")
            return
            
        print(df[["REPORT_DATE", "EPS_TTM", "BASIC_EPS", "CURRENCY"]].head(10))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    diagnose("00005") # HSBC
