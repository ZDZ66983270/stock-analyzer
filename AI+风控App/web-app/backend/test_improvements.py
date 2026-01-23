#!/usr/bin/env python3
"""
测试脚本：验证时区转换和数据去重功能

运行方式:
cd /Users/zhangzy/My\ Docs/Privates/22-AI编程/AI+风控App/web-app/backend
python3 test_improvements.py
"""

import sys
import pandas as pd
from datetime import datetime
import pytz

# 添加路径
sys.path.insert(0, '/Users/zhangzy/My Docs/Privates/22-AI编程/AI+风控App/web-app/backend')

def test_timezone_conversion():
    """测试时区转换功能"""
    print("=" * 60)
    print("测试1: 时区转换功能")
    print("=" * 60)
    
    # 创建测试数据（美东时间）
    test_data = pd.DataFrame({
        '时间': [
            '2025-12-14 09:30:00',  # 美东开盘时间
            '2025-12-14 16:00:00',  # 美东收盘时间
        ],
        'close': [100.0, 105.0]
    })
    
    print("\n原始数据（美东时间）:")
    print(test_data)
    
    # 执行时区转换
    try:
        # 转换为datetime
        test_data['时间'] = pd.to_datetime(test_data['时间'])
        
        # 本地化为美东时间
        test_data['时间'] = test_data['时间'].dt.tz_localize('US/Eastern', ambiguous='infer')
        
        # 转换为北京时间
        test_data['时间'] = test_data['时间'].dt.tz_convert('Asia/Shanghai')
        
        # 移除时区信息
        test_data['时间'] = test_data['时间'].dt.tz_localize(None)
        
        print("\n转换后数据（北京时间）:")
        print(test_data)
        
        # 验证
        expected_hour_1 = 22  # 09:30 EST = 22:30 CST (前一天)
        expected_hour_2 = 5   # 16:00 EST = 05:00 CST (次日)
        
        actual_hour_1 = test_data.iloc[0]['时间'].hour
        actual_hour_2 = test_data.iloc[1]['时间'].hour
        
        if actual_hour_1 == expected_hour_1 and actual_hour_2 == expected_hour_2:
            print("\n✅ 时区转换测试通过！")
            return True
        else:
            print(f"\n❌ 时区转换测试失败！")
            print(f"期望: {expected_hour_1}:30 和 {expected_hour_2}:00")
            print(f"实际: {actual_hour_1}:{test_data.iloc[0]['时间'].minute} 和 {actual_hour_2}:{test_data.iloc[1]['时间'].minute}")
            return False
            
    except Exception as e:
        print(f"\n❌ 时区转换出错: {e}")
        return False


def test_data_deduplication():
    """测试数据去重功能"""
    print("\n" + "=" * 60)
    print("测试2: 数据去重功能")
    print("=" * 60)
    
    from sqlmodel import select, Session
    from database import engine
    from models import MarketDataMinute
    
    with Session(engine) as session:
        # 查询某个股票的分钟数据
        stmt = select(MarketDataMinute).where(
            MarketDataMinute.symbol == '600309.SH'
        ).order_by(MarketDataMinute.date.desc()).limit(10)
        
        records = session.exec(stmt).all()
        
        if not records:
            print("❌ 没有找到测试数据")
            return False
        
        print(f"\n找到 {len(records)} 条记录")
        
        # 检查是否有重复的日期
        dates = [str(r.date) for r in records]
        unique_dates = set(dates)
        
        print(f"唯一日期数: {len(unique_dates)}")
        print(f"总记录数: {len(dates)}")
        
        if len(unique_dates) == len(dates):
            print("\n✅ 数据去重测试通过！没有重复数据")
            return True
        else:
            duplicates = len(dates) - len(unique_dates)
            print(f"\n❌ 发现 {duplicates} 条重复数据")
            return False


def test_complete_workflow():
    """测试完整的数据抓取流程"""
    print("\n" + "=" * 60)
    print("测试3: 完整数据抓取流程")
    print("=" * 60)
    
    from data_fetcher import DataFetcher
    
    fetcher = DataFetcher()
    
    # 测试抓取一个美股的分钟数据
    symbol = 'AAPL'
    
    print(f"\n抓取 {symbol} 的分钟数据...")
    
    try:
        df = fetcher.fetch_us_min_data(symbol)
        
        if df is not None and not df.empty:
            print(f"✅ 成功抓取 {len(df)} 条数据")
            print("\n前3条数据:")
            print(df.head(3))
            
            # 检查时间列
            if '时间' in df.columns:
                print(f"\n时间范围: {df['时间'].min()} 到 {df['时间'].max()}")
            
            return True
        else:
            print("❌ 没有抓取到数据")
            return False
            
    except Exception as e:
        print(f"❌ 抓取失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("开始测试数据抓取改进功能")
    print("=" * 60)
    
    results = []
    
    # 测试1: 时区转换
    results.append(("时区转换", test_timezone_conversion()))
    
    # 测试2: 数据去重
    results.append(("数据去重", test_data_deduplication()))
    
    # 测试3: 完整流程（可选，需要网络）
    # results.append(("完整流程", test_complete_workflow()))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠️ 部分测试失败，请检查")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
