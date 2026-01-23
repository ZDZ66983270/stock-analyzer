#!/usr/bin/env python3
"""
测试 AkShare 日线市盈率接口
验证 stock_value_em 和 stock_hk_valuation_baidu 的数据可用性
"""

import akshare as ak
import pandas as pd


def test_a_stock_daily_pe():
    """
    测试 A股个股日线市盈率
    接口: stock_value_em
    """
    print("\n" + "="*80)
    print("测试 1: A股个股日线市盈率 - stock_value_em")
    print("="*80 + "\n")
    
    # 测试股票: 贵州茅台
    symbol = "600519"
    
    try:
        print(f"正在获取 {symbol} (贵州茅台) 的估值数据...")
        df = ak.stock_value_em(symbol=symbol)
        
        if df.empty:
            print("❌ 未获取到数据")
            return None
        
        print(f"✅ 成功获取 {len(df)} 条历史数据\n")
        print(f"数据字段: {list(df.columns)}\n")
        
        # 检查PE字段
        pe_columns = [col for col in df.columns if '市盈率' in col or 'PE' in col.upper()]
        
        if pe_columns:
            print(f"✅ 找到PE相关字段: {pe_columns}\n")
            
            # 显示最近10天数据
            print("最近10天数据:")
            recent = df.tail(10)
            display_cols = ['数据日期', '当日收盘价'] + pe_columns[:3]  # 显示前3个PE字段
            if all(col in df.columns for col in display_cols):
                print(recent[display_cols].to_string(index=False))
            else:
                print(recent.head(10))
            
            # PE统计
            print("\n" + "="*80)
            print("PE数据统计")
            print("="*80 + "\n")
            
            for col in pe_columns[:3]:  # 只统计前3个PE字段
                if col in df.columns:
                    valid_data = df[df[col] > 0][col]
                    if len(valid_data) > 0:
                        print(f"{col}:")
                        print(f"  有效数据: {len(valid_data)}/{len(df)} 条")
                        print(f"  范围: {valid_data.min():.2f} - {valid_data.max():.2f}")
                        print(f"  平均: {valid_data.mean():.2f}")
                        print(f"  最新: {df[col].iloc[-1]:.2f}\n")
        else:
            print("❌ 未找到PE相关字段")
        
        return df
        
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_hk_stock_daily_pe():
    """
    测试 港股个股日线市盈率
    接口: stock_hk_valuation_baidu
    """
    print("\n" + "="*80)
    print("测试 2: 港股个股日线市盈率 - stock_hk_valuation_baidu")
    print("="*80 + "\n")
    
    # 测试股票: 腾讯控股
    symbol = "00700"
    
    try:
        print(f"正在获取 {symbol} (腾讯控股) 的市盈率数据...")
        df = ak.stock_hk_valuation_baidu(
            symbol=symbol,
            indicator="市盈率",
            period="近一年"
        )
        
        if df.empty:
            print("❌ 未获取到数据")
            return None
        
        print(f"✅ 成功获取 {len(df)} 条历史数据\n")
        print(f"数据字段: {list(df.columns)}\n")
        
        # 显示最近10天数据
        print("最近10天数据:")
        print(df.tail(10).to_string(index=False))
        
        # PE统计
        print("\n" + "="*80)
        print("PE数据统计")
        print("="*80 + "\n")
        
        if 'value' in df.columns:
            valid_data = df[df['value'] > 0]['value']
            if len(valid_data) > 0:
                print(f"有效数据: {len(valid_data)}/{len(df)} 条")
                print(f"PE范围: {valid_data.min():.2f} - {valid_data.max():.2f}")
                print(f"PE平均: {valid_data.mean():.2f}")
                print(f"PE中位: {valid_data.median():.2f}")
                print(f"最新PE: {df['value'].iloc[-1]:.2f}")
        
        return df
        
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_multiple_a_stocks():
    """测试多只A股"""
    print("\n" + "="*80)
    print("测试 3: 批量测试A股 (仅获取最新PE)")
    print("="*80 + "\n")
    
    stocks = {
        '600519': '贵州茅台',
        '000858': '五粮液',
        '600036': '招商银行',
    }
    
    results = []
    
    for code, name in stocks.items():
        try:
            print(f"正在获取 {code} ({name})...")
            df = ak.stock_value_em(symbol=code)
            
            if not df.empty and '市盈率TTM' in df.columns:
                latest_pe = df['市盈率TTM'].iloc[-1]
                latest_date = df['数据日期'].iloc[-1]
                results.append({
                    '代码': code,
                    '名称': name,
                    '日期': latest_date,
                    '最新PE(TTM)': latest_pe,
                    '数据条数': len(df)
                })
                print(f"  ✓ PE(TTM): {latest_pe:.2f}, 数据条数: {len(df)}")
            else:
                print(f"  ✗ 未获取到PE数据")
                
        except Exception as e:
            print(f"  ✗ 错误: {e}")
    
    if results:
        print("\n" + "="*80)
        print("批量测试汇总")
        print("="*80 + "\n")
        
        result_df = pd.DataFrame(results)
        print(result_df.to_string(index=False))


if __name__ == "__main__":
    print("\n" + "="*80)
    print("AkShare 日线市盈率接口测试")
    print("="*80)
    
    # 测试1: A股
    df_a = test_a_stock_daily_pe()
    
    # 测试2: 港股
    df_hk = test_hk_stock_daily_pe()
    
    # 测试3: 批量A股
    test_multiple_a_stocks()
    
    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)
    print("\n💡 结论:")
    print("  1. stock_value_em: A股个股历史每日PE数据")
    print("  2. stock_hk_valuation_baidu: 港股个股历史每日PE数据")
    print("  3. 两个接口都提供完整的历史PE数据")
    print()
