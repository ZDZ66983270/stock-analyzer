
import akshare as ak
import pandas as pd

def test_single_stock():
    symbol = "600519" # Moutai
    print(f"Testing AkShare single stock fetch for {symbol}...")
    
    try:
        # Candidate 1: stock_financial_analysis_indicator (Likely recent data)
        print("\n--- stock_financial_analysis_indicator ---")
        df = ak.stock_financial_analysis_indicator(symbol=symbol)
        if df is not None and not df.empty:
            print(f"Shape: {df.shape}")
            print("Columns:", df.columns.tolist()[:5])
            print("Head(1):\n", df.head(1).T)
            
        # Candidate 2: stock_financial_abstract (Sina?)
        print("\n--- stock_financial_abstract ---")
        df2 = ak.stock_financial_abstract(symbol=symbol)
        if df2 is not None and not df2.empty:
            print(f"Shape: {df2.shape}")
            pd.set_option('display.max_rows', None)
            print("Unique Indicators:\n", df2['指标'].unique())

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_single_stock()
