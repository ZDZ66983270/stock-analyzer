
import akshare as ak
import pandas as pd

def test_ratio():
    symbol = "600519"
    df = ak.stock_financial_abstract(symbol=symbol)
    if df is not None:
        idx = df[df['指标'] == '资产负债率']
        if not idx.empty:
            print("Debt Ratio Sample:", idx.iloc[0, 2]) # First date column

if __name__ == "__main__":
    test_ratio()
