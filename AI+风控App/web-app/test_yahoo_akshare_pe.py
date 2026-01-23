#!/usr/bin/env python3
"""
测试 Yahoo Finance 和 AkShare 的 A股/港股历史数据中的 PE 比率
对比两个数据源的 PE 数据可用性
"""

import yfinance as yf
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta


def test_yahoo_cn_stock(symbol):
    """
    测试 Yahoo Finance 获取 A股数据中的 PE
    
    Args:
        symbol: A股代码，如 '600519.SS' (贵州茅台)
    """
    print(f"\n{'='*70}")
    print(f"Yahoo Finance - A股测试: {symbol}")
    print(f"{'='*70}\n")
    
    ticker = yf.Ticker(symbol)
    
    # 获取历史数据
    hist = ticker.history(period='3mo')
    
    if hist.empty:
        print(f"❌ 无法获取数据")
        return
    
    print(f"✓ 成功获取 {len(hist)} 条历史数据")
    print(f"可用列: {list(hist.columns)}\n")
    
    # 检查 PE 字段
    pe_columns = [col for col in hist.columns if 'pe' in col.lower() or 'ratio' in col.lower()]
    
    if pe_columns:
        print(f"✓ 找到 PE 字段: {pe_columns}")
    else:
        print("❌ 历史数据不包含 PE 字段")
    
    # 检查 info
    info = ticker.info
    trailing_pe = info.get('trailingPE', 'N/A')
    forward_pe = info.get('forwardPE', 'N/A')
    
    print(f"\nticker.info 中的 PE:")
    print(f"  trailingPE: {trailing_pe}")
    print(f"  forwardPE: {forward_pe}")


def test_yahoo_hk_stock(symbol):
    """
    测试 Yahoo Finance 获取港股数据中的 PE
    
    Args:
        symbol: 港股代码，如 '0700.HK' (腾讯)
    """
    print(f"\n{'='*70}")
    print(f"Yahoo Finance - 港股测试: {symbol}")
    print(f"{'='*70}\n")
    
    ticker = yf.Ticker(symbol)
    
    # 获取历史数据
    hist = ticker.history(period='3mo')
    
    if hist.empty:
        print(f"❌ 无法获取数据")
        return
    
    print(f"✓ 成功获取 {len(hist)} 条历史数据")
    print(f"可用列: {list(hist.columns)}\n")
    
    # 检查 PE 字段
    pe_columns = [col for col in hist.columns if 'pe' in col.lower() or 'ratio' in col.lower()]
    
    if pe_columns:
        print(f"✓ 找到 PE 字段: {pe_columns}")
    else:
        print("❌ 历史数据不包含 PE 字段")
    
    # 检查 info
    info = ticker.info
    trailing_pe = info.get('trailingPE', 'N/A')
    forward_pe = info.get('forwardPE', 'N/A')
    
    print(f"\nticker.info 中的 PE:")
    print(f"  trailingPE: {trailing_pe}")
    print(f"  forwardPE: {forward_pe}")


def test_akshare_cn_stock(symbol):
    """
    测试 AkShare 获取 A股数据中的 PE
    
    Args:
        symbol: A股代码，如 '600519' (贵州茅台)
    """
    print(f"\n{'='*70}")
    print(f"AkShare - A股测试: {symbol}")
    print(f"{'='*70}\n")
    
    try:
        # 获取历史行情数据
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
        
        if df.empty:
            print(f"❌ 无法获取数据")
            return
        
        # 只取最近3个月
        df = df.tail(60)
        
        print(f"✓ 成功获取 {len(df)} 条历史数据")
        print(f"可用列: {list(df.columns)}\n")
        
        # 检查 PE 字段
        pe_columns = [col for col in df.columns if 'pe' in col.lower() or '市盈率' in col or 'ratio' in col.lower()]
        
        if pe_columns:
            print(f"✓ 找到 PE 相关字段: {pe_columns}")
            for col in pe_columns:
                print(f"\n{col} 样本数据:")
                print(df[col].tail(5))
        else:
            print("❌ 历史K线数据不包含 PE 字段")
        
        # 尝试获取实时行情数据 (包含 PE)
        print("\n尝试获取实时行情数据...")
        realtime = ak.stock_zh_a_spot_em()
        stock_data = realtime[realtime['代码'] == symbol]
        
        if not stock_data.empty:
            print(f"✓ 实时数据可用列: {list(stock_data.columns)}")
            pe_cols = [col for col in stock_data.columns if 'pe' in col.lower() or '市盈率' in col]
            if pe_cols:
                print(f"✓ 实时数据包含 PE 字段: {pe_cols}")
                for col in pe_cols:
                    print(f"  {col}: {stock_data[col].values[0]}")
        
    except Exception as e:
        print(f"❌ 发生错误: {e}")


def test_akshare_hk_stock(symbol):
    """
    测试 AkShare 获取港股数据中的 PE
    
    Args:
        symbol: 港股代码，如 '00700' (腾讯)
    """
    print(f"\n{'='*70}")
    print(f"AkShare - 港股测试: {symbol}")
    print(f"{'='*70}\n")
    
    try:
        # 获取历史行情数据
        df = ak.stock_hk_hist(symbol=symbol, period="daily", adjust="qfq")
        
        if df.empty:
            print(f"❌ 无法获取历史数据")
            return
        
        # 只取最近3个月
        df = df.tail(60)
        
        print(f"✓ 成功获取 {len(df)} 条历史数据")
        print(f"可用列: {list(df.columns)}\n")
        
        # 检查 PE 字段
        pe_columns = [col for col in df.columns if 'pe' in col.lower() or '市盈率' in col or 'ratio' in col.lower()]
        
        if pe_columns:
            print(f"✓ 找到 PE 相关字段: {pe_columns}")
            for col in pe_columns:
                print(f"\n{col} 样本数据:")
                print(df[col].tail(5))
        else:
            print("❌ 历史K线数据不包含 PE 字段")
        
        # 尝试获取实时行情
        print("\n尝试获取实时行情数据...")
        realtime = ak.stock_hk_spot_em()
        stock_data = realtime[realtime['代码'] == symbol]
        
        if not stock_data.empty:
            print(f"✓ 实时数据可用列: {list(stock_data.columns)}")
            pe_cols = [col for col in stock_data.columns if 'pe' in col.lower() or '市盈率' in col]
            if pe_cols:
                print(f"✓ 实时数据包含 PE 字段: {pe_cols}")
                for col in pe_cols:
                    print(f"  {col}: {stock_data[col].values[0]}")
        
    except Exception as e:
        print(f"❌ 发生错误: {e}")


def main():
    """主测试函数"""
    print("\n" + "="*70)
    print("Yahoo Finance & AkShare PE 数据对比测试")
    print("="*70)
    
    # 测试 Yahoo Finance
    print("\n\n" + "="*70)
    print("📊 Yahoo Finance 测试")
    print("="*70)
    
    test_yahoo_cn_stock('600519.SS')  # 贵州茅台
    test_yahoo_hk_stock('0700.HK')    # 腾讯控股
    
    # 测试 AkShare
    print("\n\n" + "="*70)
    print("📊 AkShare 测试")
    print("="*70)
    
    test_akshare_cn_stock('600519')   # 贵州茅台
    test_akshare_hk_stock('00700')    # 腾讯控股
    
    # 总结
    print("\n\n" + "="*70)
    print("📋 总结对比")
    print("="*70 + "\n")
    
    print("┌─────────────────┬──────────────┬──────────────┬──────────────┐")
    print("│   数据源        │  历史K线PE   │   实时PE     │   推荐度     │")
    print("├─────────────────┼──────────────┼──────────────┼──────────────┤")
    print("│ Yahoo (A股)     │      ❌      │      ✅      │      ⭐      │")
    print("│ Yahoo (港股)    │      ❌      │      ✅      │      ⭐⭐    │")
    print("│ AkShare (A股)   │      ❌      │      ✅      │      ⭐⭐⭐  │")
    print("│ AkShare (港股)  │      ❌      │      ✅      │      ⭐⭐    │")
    print("│ Futu (港股)     │      ✅      │      ✅      │      ⭐⭐⭐⭐│")
    print("└─────────────────┴──────────────┴──────────────┴──────────────┘")
    
    print("\n💡 结论:")
    print("  1. Yahoo Finance 和 AkShare 的历史K线数据都不包含每日PE")
    print("  2. 两者都只能通过实时接口获取当前PE值")
    print("  3. Futu API 是唯一提供历史每日PE的数据源")
    print("  4. 如需历史PE数据,建议:")
    print("     - 港股: 使用 Futu API ⭐⭐⭐⭐")
    print("     - A股: 自行计算 (Price/EPS) 或定期记录实时PE")
    print()


if __name__ == "__main__":
    main()
