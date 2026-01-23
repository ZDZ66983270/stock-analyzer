import sys
import os
import pandas as pd
import yfinance as yf
import akshare as ak
from datetime import datetime

# 引入 backend
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))
from symbols_config import get_yfinance_symbol

def normalize_raw_code(symbol: str) -> str:
    """归一化代码，去掉前后缀"""
    code = symbol.split(':')[-1]
    for suffix in ['.SH', '.SZ', '.SS', '.HK', '.OQ', '.N', '.O']:
        if code.upper().endswith(suffix):
            code = code[: -len(suffix)]
            break
    return code.upper()

def test_cn_financials(symbol: str):
    """测试 A 股财务数据抓取 (AkShare)"""
    raw_code = normalize_raw_code(symbol)
    print(f"\n🚀 [CN 财务测试] 对象: {symbol} -> 核心代码: {raw_code}")
    
    # 2023-12-31 是已发布的年报，更稳定
    target_date = "20231231" 
    print(f"   📅 尝试抓取 {target_date} 业绩报表 (YJBB)...")
    try:
        df = ak.stock_yjbb_em(date=target_date)
        if df is not None and not df.empty:
            # 查找目标代码
            row = df[df['股票代码'] == raw_code]
            if not row.empty:
                # 确定列名
                rev_col = '营业收入' if '营业收入' in df.columns else '营业收入-营业收入'
                net_col = '净利润' if '净利润' in df.columns else '净利润-净利润'
                print(f"   ✅ 成功抓取到业绩摘要: {rev_col} {row.iloc[0][rev_col]}，{net_col} {row.iloc[0][net_col]}")
            else:
                print(f"   ⚠️ 在该日期报表中未找到代码 {raw_code}")
        else:
            print(f"   ❌ AkShare 返回数据为空")
    except Exception as e:
        print(f"   ❌ AkShare 抓取失败: {e}")

def test_yahoo_financials(symbol: str, market: str):
    """测试港美股财务数据抓取 (Yahoo)"""
    raw_code = normalize_raw_code(symbol)
    print(f"\n🚀 [{market} 财务测试] 对象: {symbol} -> 核心代码: {raw_code}")
    
    # 转换为 Yahoo 符号
    yf_symbol = raw_code
    if market == "HK" and raw_code.isdigit():
        yf_symbol = f"{int(raw_code):04d}.HK"
    elif market == "US":
        yf_symbol = get_yfinance_symbol(symbol, market="US")
    
    print(f"   🔄 调用 Yahoo 接口 (yfinance) 符号: {yf_symbol} ...")
    try:
        ticker = yf.Ticker(yf_symbol)
        inc = ticker.financials
        if not inc.empty:
            latest_date = inc.columns[0].strftime('%Y-%m-%d')
            # 找到 Revenue 所在的行
            rev_idx = [i for i in inc.index if 'Revenue' in i]
            if rev_idx:
                rev = inc.loc[rev_idx[0], inc.columns[0]]
                print(f"   ✅ 成功抓取到 Yahoo 财报: 日期 {latest_date}，{rev_idx[0]} {rev:,.0f}")
            else:
                print(f"   ✅ 成功抓取到 Yahoo 财报: 日期 {latest_date}，但未找到 Revenue 字段")
        else:
            print(f"   ❌ Yahoo 财报数据为空")
    except Exception as e:
        print(f"   ❌ Yahoo 抓取失败: {e}")

if __name__ == "__main__":
    print("\n📊 统一财务数据抓取规则验证 (修正版)")
    
    test_cn_financials("CN:STOCK:600519")
    test_cn_financials("CN:STOCK:601998") 
    
    test_yahoo_financials("HK:STOCK:00700", "HK")
    test_yahoo_financials("US:STOCK:AAPL", "US")
    
    print(f"\n{'='*60}")
    print("🏁 财务数据抓取测试完成")
