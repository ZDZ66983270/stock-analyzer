"""
ETL功能测试脚本
测试新ETL服务的基本功能，确保数据正确流转
"""

import sys
sys.path.insert(0, '.')

from database import engine
from sqlmodel import Session, select
from models import RawMarketData, MarketDataDaily, MarketSnapshot
from etl_service import ETLService
import json
from datetime import datetime

def cleanup_test_data():
    """清理测试数据"""
    from sqlmodel import delete
    with Session(engine) as session:
        # 删除测试symbol的所有数据
        session.exec(delete(RawMarketData).where(RawMarketData.symbol == 'TEST_ETL'))
        session.exec(delete(MarketDataDaily).where(MarketDataDaily.symbol == 'TEST_ETL'))
        session.exec(delete(MarketSnapshot).where(MarketSnapshot.symbol == 'TEST_ETL'))
        session.commit()

def test_etl_basic_flow():
    """测试ETL基本流程"""
    print("=" * 60)
    print("测试1: ETL基本流程（闭市场景）")
    print("=" * 60)
    
    # 清理旧数据
    cleanup_test_data()
    
    # 1. 准备测试数据（模拟闭市后的日线数据）
    test_data = [{
        'date': '2025-12-17 16:00:00',
        'open': 100.0,
        'high': 105.0,
        'low': 99.0,
        'close': 103.0,
        'volume': 1000000
    }]
    
    print("\n步骤1: 插入RawMarketData...")
    with Session(engine) as session:
        raw = RawMarketData(
            source='test',
            symbol='TEST_ETL',
            market='US',
            period='1d',
            payload=json.dumps(test_data),
            processed=False
        )
        session.add(raw)
        session.commit()
        session.refresh(raw)
        raw_id = raw.id
        print(f"✅ RawMarketData记录已创建: ID={raw_id}")
    
    print("\n步骤2: 运行ETL处理...")
    try:
        ETLService.process_raw_data(raw_id)
        print("✅ ETL处理完成")
    except Exception as e:
        print(f"❌ ETL处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n步骤3: 验证结果...")
    with Session(engine) as session:
        # 检查processed标记
        raw = session.get(RawMarketData, raw_id)
        if raw.processed:
            print("✅ RawMarketData.processed = True")
        else:
            print("❌ RawMarketData.processed = False (应该是True)")
            return False
        
        # 检查Daily表
        daily = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.symbol == 'TEST_ETL')
        ).first()
        
        if daily:
            print(f"✅ MarketDataDaily记录已创建:")
            print(f"   close={daily.close}, volume={daily.volume}")
            if daily.close == 103.0:
                print("   ✅ 收盘价正确")
            else:
                print(f"   ❌ 收盘价错误: {daily.close} (应该是103.0)")
                return False
        else:
            print("❌ MarketDataDaily记录不存在")
            return False
        
        # 检查Snapshot表
        snapshot = session.exec(
            select(MarketSnapshot)
            .where(MarketSnapshot.symbol == 'TEST_ETL')
        ).first()
        
        if snapshot:
            print(f"✅ MarketSnapshot记录已创建:")
            print(f"   price={snapshot.price}, data_source={snapshot.data_source}")
            if snapshot.price == 103.0:
                print("   ✅ 价格正确")
            else:
                print(f"   ❌ 价格错误: {snapshot.price} (应该是103.0)")
                return False
            
            if snapshot.data_source == 'daily_close':
                print("   ✅ data_source正确 (daily_close)")
            else:
                print(f"   ⚠️  data_source={snapshot.data_source} (预期daily_close)")
        else:
            print("❌ MarketSnapshot记录不存在")
            return False
    
    print("\n" + "=" * 60)
    print("✅ 测试1通过：ETL基本流程正常")
    print("=" * 60)
    return True

def test_etl_change_calculation():
    """测试涨跌幅计算"""
    print("\n" + "=" * 60)
    print("测试2: 涨跌幅计算")
    print("=" * 60)
    
    cleanup_test_data()
    
    # 插入第一天数据
    print("\n步骤1: 插入第一天数据 (close=100)...")
    test_data_day1 = [{
        'date': '2025-12-16 16:00:00',
        'open': 98.0,
        'high': 102.0,
        'low': 97.0,
        'close': 100.0,
        'volume': 1000000
    }]
    
    with Session(engine) as session:
        raw1 = RawMarketData(
            source='test',
            symbol='TEST_ETL',
            market='US',
            period='1d',
            payload=json.dumps(test_data_day1),
            processed=False
        )
        session.add(raw1)
        session.commit()
        session.refresh(raw1)
        ETLService.process_raw_data(raw1.id)
    
    # 插入第二天数据
    print("\n步骤2: 插入第二天数据 (close=105)...")
    test_data_day2 = [{
        'date': '2025-12-17 16:00:00',
        'open': 101.0,
        'high': 106.0,
        'low': 100.0,
        'close': 105.0,
        'volume': 1200000
    }]
    
    with Session(engine) as session:
        raw2 = RawMarketData(
            source='test',
            symbol='TEST_ETL',
            market='US',
            period='1d',
            payload=json.dumps(test_data_day2),
            processed=False
        )
        session.add(raw2)
        session.commit()
        session.refresh(raw2)
        ETLService.process_raw_data(raw2.id)
    
    print("\n步骤3: 验证涨跌幅计算...")
    with Session(engine) as session:
        daily = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.symbol == 'TEST_ETL')
            .where(MarketDataDaily.date == '2025-12-17 16:00:00')
        ).first()
        
        if daily:
            expected_change = 5.0  # 105 - 100
            expected_pct = 5.0     # (5 / 100) * 100
            
            print(f"   change={daily.change} (预期{expected_change})")
            print(f"   pct_change={daily.pct_change}% (预期{expected_pct}%)")
            
            if abs(daily.change - expected_change) < 0.01:
                print("   ✅ change计算正确")
            else:
                print(f"   ❌ change计算错误")
                return False
            
            if abs(daily.pct_change - expected_pct) < 0.01:
                print("   ✅ pct_change计算正确")
            else:
                print(f"   ❌ pct_change计算错误")
                return False
        else:
            print("❌ 未找到第二天的Daily记录")
            return False
    
    print("\n" + "=" * 60)
    print("✅ 测试2通过：涨跌幅计算正确")
    print("=" * 60)
    return True

if __name__ == "__main__":
    print("\n🧪 开始ETL功能测试\n")
    
    try:
        # 测试1: 基本流程
        if not test_etl_basic_flow():
            print("\n❌ 测试失败，停止后续测试")
            sys.exit(1)
        
        # 测试2: 涨跌幅计算
        if not test_etl_change_calculation():
            print("\n❌ 测试失败")
            sys.exit(1)
        
        print("\n" + "=" * 60)
        print("🎉 所有测试通过！ETL服务工作正常")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # 清理测试数据
        print("\n清理测试数据...")
        cleanup_test_data()
        print("✅ 清理完成")
