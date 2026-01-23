#!/usr/bin/env python3
"""
港股历史K线数据获取测试 - Futu OpenAPI
测试目标：验证PE比率数据的完整性和有效性
"""

import futu as ft
import pandas as pd
from datetime import datetime, timedelta


def fetch_hk_stock_kline(stock_code, start_date, end_date, ktype=ft.KLType.K_DAY):
    """
    获取港股历史K线数据
    
    Args:
        stock_code: 股票代码，如 '09988'
        start_date: 开始日期，格式 'YYYY-MM-DD'
        end_date: 结束日期，格式 'YYYY-MM-DD'
        ktype: K线类型，默认日K线
    
    Returns:
        DataFrame: 包含K线数据的DataFrame，失败返回None
    """
    # 格式化股票代码为富途格式
    futu_code = f'HK.{stock_code}'
    
    print(f"\n{'='*62}")
    print(f"正在获取 {futu_code} 的历史K线数据...")
    print(f"时间范围: {start_date} 至 {end_date}")
    print(f"{'='*62}\n")
    
    # 创建行情上下文
    quote_ctx = ft.OpenQuoteContext(host='127.0.0.1', port=11111)
    
    try:
        # 请求历史K线数据
        ret, data, page_req_key = quote_ctx.request_history_kline(
            code=futu_code,
            start=start_date,
            end=end_date,
            ktype=ktype,
            autype=ft.AuType.QFQ,  # 前复权
            max_count=1000
        )
        
        if ret == ft.RET_OK:
            print(f"✓ 成功获取 {len(data)} 条K线数据\n")
            print(f"数据列: {list(data.columns)}\n")
            return data
        else:
            print(f"✗ 获取数据失败: {data}")
            return None
            
    except Exception as e:
        print(f"✗ 发生异常: {e}")
        return None
        
    finally:
        quote_ctx.close()


def analyze_pe_data(data, stock_code):
    """
    分析PE比率数据
    
    Args:
        data: K线数据DataFrame
        stock_code: 股票代码
    """
    if data is None or data.empty:
        print("⚠️  无数据可分析")
        return
    
    # 检查PE字段是否存在
    if 'pe_ratio' not in data.columns:
        print("⚠️  警告: 数据中不包含 'pe_ratio' 字段")
        print(f"可用字段: {list(data.columns)}")
        return
    
    print("✓ PE比率字段存在\n")
    
    # PE统计信息
    print("PE比率统计信息:")
    print(data['pe_ratio'].describe())
    print()
    
    # PE有效性分析
    pe_positive = (data['pe_ratio'] > 0).sum()
    pe_zero = (data['pe_ratio'] == 0).sum()
    pe_negative = (data['pe_ratio'] < 0).sum()
    total = len(data)
    
    print(f"PE > 0 的数据条数: {pe_positive} / {total}")
    print(f"PE = 0 的数据条数: {pe_zero}")
    print(f"PE < 0 的数据条数: {pe_negative}")
    print()
    
    # 详细分析
    print(f"\n{'='*62}")
    print(f"{stock_code} PE数据详细分析")
    print(f"{'='*62}\n")
    
    print("1. PE值分布:")
    print(f"   PE = 0:  {pe_zero:4d} 条 ({pe_zero/total*100:.1f}%)")
    print(f"   PE > 0:  {pe_positive:4d} 条 ({pe_positive/total*100:.1f}%)")
    print(f"   PE < 0:  {pe_negative:4d} 条 ({pe_negative/total*100:.1f}%)")
    print()
    
    # 有效PE数据统计
    valid_pe = data[data['pe_ratio'] > 0]['pe_ratio']
    if len(valid_pe) > 0:
        print("2. 有效PE数据统计 (PE > 0):")
        print(f"   最小值: {valid_pe.min():.2f}")
        print(f"   最大值: {valid_pe.max():.2f}")
        print(f"   平均值: {valid_pe.mean():.2f}")
        print(f"   中位数: {valid_pe.median():.2f}")
        print()
    
    # 最近30天PE趋势
    recent_data = data.tail(min(30, len(data)))
    print("3. 最近30天PE趋势:")
    print(recent_data[['time_key', 'close', 'pe_ratio']].to_string(index=False))
    print()


def test_multiple_stocks(stock_codes, start_date, end_date):
    """
    测试多只股票的数据获取
    
    Args:
        stock_codes: 股票代码列表
        start_date: 开始日期
        end_date: 结束日期
    """
    results = {}
    
    for stock_code in stock_codes:
        data = fetch_hk_stock_kline(stock_code, start_date, end_date)
        results[stock_code] = data
        
        if data is not None:
            analyze_pe_data(data, stock_code)
        
        print("\n" + "="*62 + "\n")
    
    # 汇总统计
    print("\n" + "="*62)
    print("批量测试汇总")
    print("="*62 + "\n")
    
    for stock_code, data in results.items():
        if data is not None:
            pe_valid = (data['pe_ratio'] > 0).sum() if 'pe_ratio' in data.columns else 0
            total = len(data)
            print(f"{stock_code}: {total} 条数据, PE有效率 {pe_valid/total*100:.1f}%")
        else:
            print(f"{stock_code}: 获取失败")


def main():
    """主函数"""
    print("\n" + "="*62)
    print("港股历史K线数据获取测试 - Futu OpenAPI")
    print("="*62)
    
    # 测试股票列表
    stocks = [
        '09988',  # 阿里巴巴-SW
        '00005',  # 汇丰控股
    ]
    
    # 时间范围：最近3个月
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    
    print(f"\n测试配置:")
    print(f"  股票代码: {', '.join(stocks)}")
    print(f"  时间范围: {start_date} 至 {end_date}")
    print(f"  K线类型: 日K线")
    print(f"  复权方式: 前复权")
    print()
    
    # 执行测试
    test_multiple_stocks(stocks, start_date, end_date)
    
    print("\n✓ 测试完成")
    print("\n💡 提示:")
    print("  - 如需测试更多股票，请修改 stocks 列表")
    print("  - 如需调整时间范围，请修改 timedelta(days=90)")
    print("  - 如需使用周K线，请在调用时传入 ktype=ft.KLType.K_WEEK")
    print()


if __name__ == "__main__":
    main()
