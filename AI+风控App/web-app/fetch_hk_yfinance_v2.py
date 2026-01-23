"""
测试从Yahoo Finance获取HK指数数据 (使用正确Symbol)
验证是否有 2025-12-17 的数据
"""
import yfinance as yf
from datetime import datetime

print("=" * 60)
print("📥 Testing Yahoo Finance for HK Indices (Correct Symbols)")
print("=" * 60)

indices = [
    {"symbol": "^HSI", "name": "恒生指数"},
    {"symbol": "HSTECH.HK", "name": "恒生科技指数"}, # Corrected symbol
]

for item in indices:
    symbol = item['symbol']
    name = item['name']
    
    print(f"\n[{name}] ({symbol})")
    print("-" * 60)
    
    try:
        ticker = yf.Ticker(symbol)
        # 获取最近5天数据
        df = ticker.history(period="5d")
        
        if df.empty:
            print("❌ 无数据 (No data found)")
            continue
            
        print(f"✅ 获取到 {len(df)} 条记录")
        print(f"Latest records:")
        for date, row in df.iterrows():
            date_str = date.strftime('%Y-%m-%d')
            close = row['Close']
            print(f"  {date_str}: {close:.2f}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "=" * 60)
