import sys
import os
import pandas as pd
import akshare as ak
import yfinance as yf
import logging

# 引入 backend 路径以使用 symbols_config 中的工具
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))
from symbols_config import SYMBOLS_CONFIG, get_yfinance_symbol, get_akshare_symbol

# 设置日志
logging.basicConfig(level=logging.ERROR)

def normalize_raw_code(symbol: str) -> str:
    """
    1. 自动去掉前缀 (如 CN:STOCK:)
    2. 自动去掉后缀 (如 .SH, .SS, .HK, .OQ)
    """
    # 去前缀
    code = symbol.split(':')[-1]
    
    # 去常见后缀
    for suffix in ['.SH', '.SZ', '.SS', '.HK', '.OQ', '.N', '.O', '.BJ']:
        if code.upper().endswith(suffix):
            code = code[: -len(suffix)]
            break
            
    return code.upper()

def test_fetch_strategy(symbol: str, market: str, category: str):
    """
    根据规则进行抓取测试并打印结果
    """
    raw_code = normalize_raw_code(symbol)
    print(f"\n{'='*60}")
    print(f"🔍 测试对象: {symbol} | 归一化代码: {raw_code}")
    print(f"📍 市场: {market} | 分类: {category}")
    print(f"{'-'*60}")

    if market == "CN":
        # A股优先使用 AkShare
        print(f"🚀 [CN 策略] 优先调用 AkShare...")
        try:
            if category == "index":
                ak_sym = get_akshare_symbol(raw_code)
                df = ak.stock_zh_index_daily(symbol=ak_sym)
            elif category == "etf":
                df = ak.stock_zh_a_hist_min_em(symbol=raw_code)
            else:
                df = ak.stock_zh_a_hist(symbol=raw_code, period="daily", adjust="qfq")
            
            if not df.empty:
                print(f"✅ AkShare 成功 | 获取到 {len(df)} 条记录 | 最新价: {df.iloc[-1].get('收盘', df.iloc[-1].get('close', 'N/A'))}")
            else:
                print(f"⚠️ AkShare 返回空数据")
        except Exception as e:
            print(f"❌ AkShare 失败: {e}")
            
    elif market in ["HK", "US"]:
        # 港美股优先使用 Yahoo
        print(f"🚀 [{market} 策略] 优先调用 Yahoo (yfinance)...")
        try:
            # 港股需要特殊补全
            yf_sym = raw_code
            if market == "HK" and raw_code.isdigit():
                yf_sym = f"{int(raw_code):04d}.HK"
            elif market == "US":
                # 检查是否存在显式映射
                yf_sym = get_yfinance_symbol(raw_code, market="US")
            
            ticker = yf.Ticker(yf_sym)
            df = ticker.history(period="5d") # 取最近5天防止周末
            if not df.empty:
                print(f"✅ Yahoo 成功 | 符号: {yf_sym} | 最新收盘: {df['Close'].iloc[-1]:.2f}")
            else:
                print(f"⚠️ Yahoo 返回空数据")
        except Exception as e:
            print(f"❌ Yahoo 失败: {e}")

# 定义测试案例
test_cases = [
    # A股: 个股, ETF, 指数
    {"symbol": "CN:STOCK:600519", "market": "CN", "category": "stock"},
    {"symbol": "CN:ETF:159662", "market": "CN", "category": "etf"},
    {"symbol": "CN:INDEX:000300", "market": "CN", "category": "index"},
    
    # 港股: 个股, ETF, 指数
    {"symbol": "HK:STOCK:00700", "market": "HK", "category": "stock"},
    {"symbol": "HK:ETF:02800", "market": "HK", "category": "etf"},
    {"symbol": "HK:INDEX:HSI", "market": "HK", "category": "index"},
    
    # 美股: 个股, ETF, 指数
    {"symbol": "US:STOCK:AAPL", "market": "US", "category": "stock"},
    {"symbol": "US:ETF:SPY", "market": "US", "category": "etf"},
    {"symbol": "US:INDEX:SPX", "market": "US", "category": "index"},
]

if __name__ == "__main__":
    print("\n📊 统一数据抓取规则验证工具")
    for case in test_cases:
        test_fetch_strategy(case["symbol"], case["market"], case["category"])
    print(f"\n{'='*60}")
    print("🏁 测试完成")
