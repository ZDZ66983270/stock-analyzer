import akshare as ak

# Test what columns AkShare actually returns
df = ak.stock_zh_index_daily_em(symbol="sh000016")
print("Columns returned by AkShare:")
print(df.columns.tolist())
print("\nFirst row:")
print(df.iloc[0])
