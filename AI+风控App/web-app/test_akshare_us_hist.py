#!/usr/bin/env python3
"""
测试 AkShare 美股历史K线数据 - 验证是否包含 PE 比率
测试 Big 7 + TSM 的历史数据
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta


def test_akshare_us_stock_hist(symbol, name_cn):
    """
    测试 AkShare 美股历史K线接口
    
    接口: stock_us_hist
    参数: symbol (如 '105.AAPL'), period (daily/weekly/monthly), adjust (qfq/hfq/none)
    """
    print(f"\n{'='*80}")
    print(f"测试股票: {symbol} ({name_cn})")
    print(f"{'='*80}\n")
    
    try:
        # 获取历史数据 - 最近3个月
        print(f"正在调用 AkShare API: stock_us_hist(symbol='{symbol}', period='daily')...")
        
        df = ak.stock_us_hist(
            symbol=symbol,
            period="daily",
            start_date=(datetime.now() - timedelta(days=90)).strftime('%Y%m%d'),
            end_date=datetime.now().strftime('%Y%m%d'),
            adjust=""  # 不复权
        )
        
        if df.empty:
            print(f"❌ 未获取到数据")
            return None
        
        print(f"✓ 成功获取 {len(df)} 条历史数据\n")
        print(f"数据字段: {list(df.columns)}\n")
        
        # 检查是否包含 PE 字段
        pe_columns = [col for col in df.columns if 'pe' in col.lower() or '市盈率' in col or 'ratio' in col.lower()]
        
        if pe_columns:
            print(f"✅ 找到 PE 相关字段: {pe_columns}\n")
            for col in pe_columns:
                print(f"{col} 统计:")
                print(df[col].describe())
                print()
        else:
            print("❌ 历史K线数据不包含 PE 字段\n")
        
        # 显示最近10天数据
        print("最近10天数据样本:")
        recent = df.tail(10)
        display_cols = [col for col in ['日期', '开盘', '收盘', '最高', '最低', '成交量'] if col in df.columns]
        if display_cols:
            print(recent[display_cols].to_string(index=False))
        else:
            print(recent.head(10))
        
        return df
        
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_big7_tsm():
    """测试 Big 7 + TSM 的历史数据"""
    print("\n" + "="*80)
    print("AkShare 美股历史K线数据测试 - Big 7 + TSM")
    print("="*80)
    
    # Big 7 + TSM - 使用 AkShare 的代码格式
    # 根据之前的测试,AkShare 使用 "105.MSFT" 这样的格式
    stocks = [
        ('105.AAPL', 'AAPL', '苹果'),
        ('105.MSFT', 'MSFT', '微软'),
        ('105.GOOGL', 'GOOGL', '谷歌'),  # 或 105.GOOG
        ('105.NVDA', 'NVDA', '英伟达'),
        ('105.TSLA', 'TSLA', '特斯拉'),
        ('105.META', 'META', 'Meta'),
        ('105.AMZN', 'AMZN', '亚马逊'),
        ('105.TSM', 'TSM', '台积电'),
    ]
    
    print("\n目标股票:")
    for ak_code, std_code, name in stocks:
        print(f"  {std_code:6s} ({ak_code:12s}) - {name}")
    
    print("\n" + "="*80)
    print("开始测试 (仅测试前2只以节省时间)")
    print("="*80)
    
    results = []
    
    # 只测试前2只股票
    for ak_code, std_code, name in stocks[:2]:
        df = test_akshare_us_stock_hist(ak_code, name)
        
        if df is not None:
            has_pe = any('pe' in col.lower() or '市盈率' in col for col in df.columns)
            results.append({
                '代码': std_code,
                '名称': name,
                'AkShare代码': ak_code,
                '数据条数': len(df),
                '包含PE': '✅' if has_pe else '❌'
            })
    
    # 显示汇总
    if results:
        print("\n" + "="*80)
        print("测试汇总")
        print("="*80 + "\n")
        
        result_df = pd.DataFrame(results)
        print(result_df.to_string(index=False))


if __name__ == "__main__":
    test_big7_tsm()
    
    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)
    print("\n💡 结论:")
    print("  - 测试 AkShare 美股历史K线接口: stock_us_hist()")
    print("  - 验证历史数据是否包含每日 PE 比率")
    print("  - 对比 yfinance 和 Futu API 的数据完整性")
    print()
