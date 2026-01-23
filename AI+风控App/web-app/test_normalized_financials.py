import sys
import os
import pandas as pd
import akshare as ak
import yfinance as yf
import logging

# 禁用冗余日志
logging.basicConfig(level=logging.ERROR)

def normalize_raw_code(symbol: str) -> str:
    """提取核心代码（去掉前缀和后缀）"""
    code = symbol.split(':')[-1]
    for suffix in ['.SH', '.SZ', '.SS', '.HK', '.OQ', '.N', '.O', '.BJ']:
        if code.upper().endswith(suffix):
            code = code[: -len(suffix)]
            break
    return code.upper()

def test_financial_fetching(symbol: str, market: str):
    """验证归一化后的代码在财务接口上的连通性"""
    raw_code = normalize_raw_code(symbol)
    print(f"\n🧪 [测试] {symbol} (市场: {market})")
    print(f"   归一化处理 -> 核心代码: {raw_code}")

    if market == "CN":
        # A股优先使用 AkShare (财务摘要接口)
        print(f"   🚀 策略: 调用 AkShare (CN 财务接口)...")
        try:
            df = ak.stock_financial_abstract_em(symbol=raw_code)
            if df is not None and not df.empty:
                print(f"   ✅ 成功: 抓取到 {len(df)} 行财务摘要数据")
            else:
                print(f"   ❌ 失败: 返回数据为空")
        except Exception as e:
            print(f"   ❌ 错误: {e}")

    elif market in ["HK", "US"]:
        # 港美股优先使用 Yahoo
        yf_code = raw_code
        if market == "HK" and raw_code.isdigit():
            yf_code = f"{int(raw_code):04d}.HK"
            
        print(f"   🚀 策略: 调用 Yahoo (Yahoo 财务接口) 符号: {yf_code}...")
        try:
            ticker = yf.Ticker(yf_code)
            df = ticker.financials
            if df is not None and not df.empty:
                print(f"   ✅ 成功: 抓取到财务报表 (包含日期: {', '.join([d.strftime('%Y-%m-%d') for d in df.columns[:2]])} ...)")
            else:
                print(f"   ❌ 失败: 返回数据为空")
        except Exception as e:
            print(f"   ❌ 错误: {e}")

if __name__ == "__main__":
    print("📊 财务抓取规则验证 (仅测试连通性)")
    
    # 定义核心测试案例 (选取个股，因为 ETF/指数通常无财报)
    cases = [
        {"symbol": "CN:STOCK:600519", "market": "CN"},
        {"symbol": "HK:STOCK:00700", "market": "HK"},
        {"symbol": "US:STOCK:AAPL", "market": "US"},
    ]
    
    for c in cases:
        test_financial_fetching(c["symbol"], c["market"])
        
    print("\n" + "="*60)
    print("🏁 财务接口归一化规则验证完成")
