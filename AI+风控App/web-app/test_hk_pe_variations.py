#!/usr/bin/env python3
"""
测试 stock_hk_valuation_baidu 接口的不同参数格式
尝试找到正确的调用方式
"""

import akshare as ak
import pandas as pd


def test_hk_valuation_variations():
    """测试不同的参数组合"""
    print("\n" + "="*80)
    print("测试 stock_hk_valuation_baidu 不同参数格式")
    print("="*80 + "\n")
    
    # 测试股票列表
    test_symbols = ["00700", "06969", "09988"]
    
    # 测试指标列表
    indicators = ["市盈率", "总市值", "市净率", "市销率", "市现率", "股息率"]
    
    # 测试周期列表
    periods = ["近一年", "近三年", "近五年", "全部"]
    
    results = []
    
    # 测试1: 尝试不同股票代码
    print("测试1: 尝试不同股票代码\n")
    for symbol in test_symbols:
        print(f"测试股票: {symbol}")
        try:
            df = ak.stock_hk_valuation_baidu(
                symbol=symbol,
                indicator="市盈率",
                period="近一年"
            )
            if df is not None and not df.empty:
                print(f"  ✓ 成功! 获取 {len(df)} 条数据")
                results.append({
                    'symbol': symbol,
                    'indicator': '市盈率',
                    'period': '近一年',
                    'status': '成功',
                    'rows': len(df)
                })
            else:
                print(f"  ✗ 返回空数据")
                results.append({
                    'symbol': symbol,
                    'indicator': '市盈率',
                    'period': '近一年',
                    'status': '空数据',
                    'rows': 0
                })
        except Exception as e:
            print(f"  ✗ 错误: {str(e)[:100]}")
            results.append({
                'symbol': symbol,
                'indicator': '市盈率',
                'period': '近一年',
                'status': f'错误: {str(e)[:50]}',
                'rows': 0
            })
        print()
    
    # 测试2: 尝试不同指标
    print("\n" + "="*80)
    print("测试2: 尝试不同指标 (使用 00700)")
    print("="*80 + "\n")
    
    for indicator in indicators:
        print(f"测试指标: {indicator}")
        try:
            df = ak.stock_hk_valuation_baidu(
                symbol="00700",
                indicator=indicator,
                period="近一年"
            )
            if df is not None and not df.empty:
                print(f"  ✓ 成功! 获取 {len(df)} 条数据")
                print(f"  字段: {list(df.columns)}")
                print(f"  样本: {df.head(2).to_dict('records')}")
            else:
                print(f"  ✗ 返回空数据")
        except Exception as e:
            print(f"  ✗ 错误: {str(e)[:100]}")
        print()
    
    # 测试3: 尝试不同周期
    print("\n" + "="*80)
    print("测试3: 尝试不同周期 (使用 00700, 市盈率)")
    print("="*80 + "\n")
    
    for period in periods:
        print(f"测试周期: {period}")
        try:
            df = ak.stock_hk_valuation_baidu(
                symbol="00700",
                indicator="市盈率",
                period=period
            )
            if df is not None and not df.empty:
                print(f"  ✓ 成功! 获取 {len(df)} 条数据")
            else:
                print(f"  ✗ 返回空数据")
        except Exception as e:
            print(f"  ✗ 错误: {str(e)[:100]}")
        print()
    
    # 显示汇总
    if results:
        print("\n" + "="*80)
        print("测试汇总")
        print("="*80 + "\n")
        
        result_df = pd.DataFrame(results)
        print(result_df.to_string(index=False))


def test_alternative_hk_interface():
    """测试备选的港股接口"""
    print("\n" + "="*80)
    print("测试备选接口: stock_hk_indicator_eniu")
    print("="*80 + "\n")
    
    symbol = "hk00700"
    indicators = ["市盈率", "市净率", "股息率", "ROE", "市值"]
    
    for indicator in indicators:
        print(f"测试 {symbol} - {indicator}")
        try:
            df = ak.stock_hk_indicator_eniu(symbol=symbol, indicator=indicator)
            if df is not None and not df.empty:
                print(f"  ✓ 成功! 获取 {len(df)} 条数据")
                print(f"  字段: {list(df.columns)}")
                print(f"  最近5条:")
                print(df.tail(5).to_string(index=False))
            else:
                print(f"  ✗ 返回空数据")
        except Exception as e:
            print(f"  ✗ 错误: {str(e)[:100]}")
        print()


if __name__ == "__main__":
    print("\n" + "="*80)
    print("港股PE数据接口测试")
    print("="*80)
    
    # 测试主接口
    test_hk_valuation_variations()
    
    # 测试备选接口
    test_alternative_hk_interface()
    
    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)
    print("\n💡 结论:")
    print("  - 如果两个接口都失败,建议使用 Futu API")
    print("  - Futu API 已验证100%可用于港股PE数据")
    print()
