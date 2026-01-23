#!/usr/bin/env python3
"""
测试汇丰控股的不同代码格式
"""
import yfinance as yf

print("=" * 80)
print("测试汇丰控股的不同代码格式")
print("=" * 80)

# 测试不同格式
test_symbols = [
    ("00005.HK", "5位数字 + .HK"),
    ("0005.HK", "4位数字 + .HK"),
    ("5.HK", "1位数字 + .HK"),
    ("HSBC", "纯英文代码"),
]

for symbol, desc in test_symbols:
    print(f"\n📊 测试: {symbol} ({desc})")
    print("-" * 80)
    
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="5d")
        
        if not hist.empty:
            latest = hist.iloc[-1]
            info = ticker.info
            
            print(f"✅ 成功!")
            print(f"   公司名: {info.get('longName', 'N/A')}")
            print(f"   最新价: {latest['Close']:.2f}")
            print(f"   日期: {latest.name.strftime('%Y-%m-%d')}")
            print(f"   成交量: {int(latest['Volume']):,}")
        else:
            print(f"❌ 无数据")
            
    except Exception as e:
        print(f"❌ 错误: {e}")

print("\n" + "=" * 80)
