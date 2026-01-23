"""
测试恒生科技指数(HSTECH)的yfinance代码映射
"""
import sys
sys.path.insert(0, 'backend')

from symbols_config import get_yfinance_symbol, get_symbol_info
from models import Index
from database import engine
from sqlmodel import Session, select

print("="*70)
print("恒生科技指数 yfinance 代码映射测试")
print("="*70)

# 1. 从Index表获取HSTECH配置
print("\n1️⃣  Index表中的HSTECH配置")
print("-"*70)
with Session(engine) as session:
    hstech = session.exec(
        select(Index).where(Index.symbol == "HSTECH")
    ).first()
    
    if hstech:
        print(f"   Symbol: {hstech.symbol}")
        print(f"   Name: {hstech.name}")
        print(f"   Market: {hstech.market}")
    else:
        print("   ❌ HSTECH 未在Index表中找到")

# 2. symbols_config中的映射
print("\n2️⃣  symbols_config.py 中的映射")
print("-"*70)
yf_symbol = get_yfinance_symbol("HSTECH")
print(f"   内部代码: HSTECH")
print(f"   yfinance代码: {yf_symbol}")

# 3. 完整配置信息
print("\n3️⃣  完整配置信息")
print("-"*70)
config = get_symbol_info("HSTECH")
if config:
    print(f"   Market: {config.get('market')}")
    print(f"   Type: {config.get('type')}")
    print(f"   yfinance_symbol: {config.get('yfinance_symbol')}")
    print(f"   akshare_symbol: {config.get('akshare_symbol')}")
    print(f"   Name (CN): {config.get('name')}")
    print(f"   Name (EN): {config.get('name_en')}")
    print(f"   Data Sources: {config.get('data_sources')}")
else:
    print("   ❌ 未找到配置")

# 4. 测试yfinance下载
print("\n4️⃣  测试 yfinance 下载")
print("-"*70)
print(f"   将使用代码: {yf_symbol}")
print(f"   测试下载...")

try:
    import yfinance as yf
    ticker = yf.Ticker(yf_symbol)
    hist = ticker.history(period="5d")
    
    if not hist.empty:
        print(f"   ✅ 成功获取 {len(hist)} 天数据")
        print(f"\n   最新数据:")
        latest = hist.iloc[-1]
        print(f"      日期: {hist.index[-1]}")
        print(f"      收盘价: {latest['Close']:.2f}")
        print(f"      成交量: {latest['Volume']:,.0f}")
    else:
        print(f"   ❌ 未获取到数据")
except Exception as e:
    print(f"   ❌ 下载失败: {e}")

print("\n" + "="*70)
print("总结")
print("="*70)
print(f"\n当系统下载恒生科技指数时:")
print(f"   1. 从Index表读取: symbol='HSTECH', market='HK'")
print(f"   2. 查询symbols_config映射: HSTECH → {yf_symbol}")
print(f"   3. 向yfinance发送请求: yf.Ticker('{yf_symbol}')")
print(f"   4. 获取历史数据: ticker.history()")
print("\n✅ 测试完成！")
