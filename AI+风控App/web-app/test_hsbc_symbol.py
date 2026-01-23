#!/usr/bin/env python3
"""
测试汇丰控股的代码转换和数据获取
"""
import yfinance as yf

print("=" * 80)
print("汇丰控股 (HSBC) 代码转换测试")
print("=" * 80)

# 数据库中存储的代码
db_symbol = "00005.HK"
print(f"\n📊 数据库存储代码: {db_symbol}")

# yfinance 转换逻辑（参考 data_fetcher.py 第147-148行）
def convert_to_yfinance(symbol, market):
    """模拟 _convert_to_yfinance_symbol 方法"""
    s = symbol.strip().upper()
    if "." in s:
        return s  # 已经有后缀
    
    if market == "HK":
        # 纯数字则补齐5位 加 .HK
        if s.isdigit():
            return f"{int(s):05d}.HK"
        return f"{s}.HK"
    
    return s

# 测试转换
yf_symbol = convert_to_yfinance(db_symbol, "HK")
print(f"🔄 yfinance 转换后: {yf_symbol}")

# 实际测试数据获取
print(f"\n🌐 测试 yfinance 数据获取...")
print(f"   使用代码: {yf_symbol}")

try:
    ticker = yf.Ticker(yf_symbol)
    
    # 获取最新行情
    hist = ticker.history(period="5d")
    
    if not hist.empty:
        latest = hist.iloc[-1]
        print(f"\n✅ 数据获取成功!")
        print(f"   最新收盘价: {latest['Close']:.2f}")
        print(f"   日期: {latest.name.strftime('%Y-%m-%d')}")
        print(f"   成交量: {int(latest['Volume']):,}")
    else:
        print(f"\n❌ 未获取到数据")
    
    # 获取公司信息
    info = ticker.info
    print(f"\n📋 公司信息:")
    print(f"   名称: {info.get('longName', 'N/A')}")
    print(f"   市场: {info.get('exchange', 'N/A')}")
    print(f"   货币: {info.get('currency', 'N/A')}")
    
except Exception as e:
    print(f"\n❌ 错误: {e}")

print("\n" + "=" * 80)
print("总结:")
print("=" * 80)
print(f"""
1. 数据库存储: {db_symbol}
2. yfinance 使用: {yf_symbol}
3. 转换逻辑: 
   - 如果代码已有后缀 (.HK)，直接使用
   - 如果是纯数字，补齐5位后加 .HK
   - 汇丰的情况: 00005.HK 已有后缀，直接使用

结论: 获取汇丰行情时使用的代码是 **{yf_symbol}**
""")
