#!/usr/bin/env python3
"""
测试 yfinance 美股历史日线数据中的 PE 比率
验证每天的数据是否都包含 PE 比率
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


def test_yfinance_pe_data(symbol, period='3mo'):
    """
    测试 yfinance 获取的美股数据中是否包含 PE 比率
    
    Args:
        symbol: 股票代码，如 'AAPL'
        period: 时间范围，如 '3mo', '1y', 'max'
    """
    print(f"\n{'='*70}")
    print(f"测试股票: {symbol}")
    print(f"时间范围: {period}")
    print(f"{'='*70}\n")
    
    # 创建 Ticker 对象
    ticker = yf.Ticker(symbol)
    
    # 1. 获取历史数据
    print("1. 获取历史K线数据...")
    hist = ticker.history(period=period)
    
    if hist.empty:
        print(f"❌ 无法获取 {symbol} 的历史数据")
        return
    
    print(f"✓ 成功获取 {len(hist)} 条历史数据")
    print(f"\n可用列: {list(hist.columns)}")
    
    # 2. 检查是否有 PE 相关字段
    print(f"\n{'='*70}")
    print("2. 检查历史数据中的 PE 字段")
    print(f"{'='*70}\n")
    
    pe_columns = [col for col in hist.columns if 'pe' in col.lower() or 'ratio' in col.lower()]
    
    if pe_columns:
        print(f"✓ 找到 PE 相关字段: {pe_columns}")
        for col in pe_columns:
            print(f"\n{col} 统计:")
            print(hist[col].describe())
    else:
        print("❌ 历史K线数据中不包含 PE 字段")
    
    # 3. 获取 info 中的 PE 数据
    print(f"\n{'='*70}")
    print("3. 检查 ticker.info 中的 PE 数据")
    print(f"{'='*70}\n")
    
    info = ticker.info
    
    pe_keys = ['trailingPE', 'forwardPE', 'trailingPegRatio']
    
    print("当前 PE 相关指标:")
    for key in pe_keys:
        value = info.get(key, 'N/A')
        print(f"  {key}: {value}")
    
    # 4. 显示最近几天的数据样本
    print(f"\n{'='*70}")
    print("4. 最近10天数据样本")
    print(f"{'='*70}\n")
    
    recent = hist.tail(10)
    print(recent[['Open', 'High', 'Low', 'Close', 'Volume']])
    
    # 5. 结论
    print(f"\n{'='*70}")
    print("结论")
    print(f"{'='*70}\n")
    
    if pe_columns:
        print("✓ yfinance 历史数据包含 PE 字段")
        print(f"  字段名: {pe_columns}")
    else:
        print("❌ yfinance 历史K线数据不包含 PE 字段")
        print("✓ 但可以从 ticker.info 获取当前 PE 值")
        print("  - trailingPE: 静态市盈率 (基于过去12个月)")
        print("  - forwardPE: 动态市盈率 (基于未来预期)")
        
        if info.get('trailingPE'):
            print(f"\n💡 建议: 使用 ticker.info['trailingPE'] 获取当前PE")
            print(f"   当前值: {info.get('trailingPE')}")


def test_multiple_stocks():
    """测试多只美股"""
    stocks = [
        'AAPL',   # 苹果
        'MSFT',   # 微软
        'GOOGL',  # 谷歌
        'TSLA',   # 特斯拉
    ]
    
    print("\n" + "="*70)
    print("yfinance 美股 PE 数据测试")
    print("="*70)
    
    for stock in stocks:
        test_yfinance_pe_data(stock, period='3mo')
        print("\n")
    
    # 总结
    print("\n" + "="*70)
    print("总结")
    print("="*70 + "\n")
    
    print("📊 yfinance API 的 PE 数据获取方式:\n")
    print("1. ❌ 历史K线数据 (ticker.history())")
    print("   - 不包含每日的 PE 比率")
    print("   - 只有 OHLCV (开高低收量) 数据\n")
    
    print("2. ✓ 实时快照数据 (ticker.info)")
    print("   - 包含当前的 PE 比率")
    print("   - trailingPE: 静态市盈率")
    print("   - forwardPE: 动态市盈率\n")
    
    print("3. 💡 如需历史每日PE数据:")
    print("   - 方案A: 使用财报数据自行计算 (EPS × Price)")
    print("   - 方案B: 使用其他数据源 (如 Futu API)")
    print("   - 方案C: 定期记录 ticker.info 的 PE 值到数据库\n")


if __name__ == "__main__":
    test_multiple_stocks()
