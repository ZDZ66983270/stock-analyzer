#!/usr/bin/env python3
"""
数据下载完整性验证测试套件 v2.0
包含常规测试 + 最新修复问题的专项验证
"""
import sys
import os
from datetime import datetime

sys.path.append(os.path.join(os.getcwd(), 'backend'))
from database import engine
from sqlmodel import Session, select, func
from models import Watchlist, Index, MarketDataDaily, FinancialFundamentals, MarketSnapshot

def test_id_format_correctness():
    """测试1: 验证关键资产的 Canonical ID 格式"""
    print("\n" + "="*60)
    print("测试1: Canonical ID 格式验证")
    print("="*60)
    
    critical_assets = {
        'TLT': 'US:ETF:TLT',
        '000001': 'CN:INDEX:000001',
        '600030': 'CN:STOCK:600030',
        'AAPL': 'US:STOCK:AAPL',
        'HSI': 'HK:INDEX:HSI',
    }
    
    with Session(engine) as session:
        all_pass = True
        for code, expected_id in critical_assets.items():
            item = session.exec(
                select(Watchlist).where(Watchlist.symbol == expected_id)
            ).first()
            
            if not item:
                item = session.exec(
                    select(Index).where(Index.symbol == expected_id)
                ).first()
            
            if item:
                print(f"✅ [{code}] -> {item.symbol} (正确)")
            else:
                print(f"❌ [{code}] -> 未找到 {expected_id}")
                all_pass = False
        
        return all_pass

def test_hk_index_code_normalization():
    """测试2: 验证 HK 指数代码规范化（新增）"""
    print("\n" + "="*60)
    print("测试2: HK 指数代码规范化验证")
    print("="*60)
    
    # 验证新的规范化代码存在
    expected_codes = {
        'HK:INDEX:HSCC': '红筹指数',
        'HK:INDEX:HSCE': '国企指数',
        'HK:INDEX:HSI': '恒生指数',
        'HK:INDEX:HSTECH': '恒生科技指数'
    }
    
    # 验证旧代码不存在
    old_codes = ['HK:INDEX:0HSCC', 'HK:INDEX:0HSCE']
    
    with Session(engine) as session:
        all_pass = True
        
        # 检查新代码
        print("\n✓ 检查规范化代码：")
        for code, name in expected_codes.items():
            item = session.exec(
                select(Index).where(Index.symbol == code)
            ).first()
            
            if item:
                print(f"  ✅ {code} ({name}) - 存在")
            else:
                print(f"  ❌ {code} ({name}) - 缺失")
                all_pass = False
        
        # 检查旧代码不存在
        print("\n✓ 检查旧代码已清除：")
        for code in old_codes:
            item = session.exec(
                select(Index).where(Index.symbol == code)
            ).first()
            
            if item:
                print(f"  ❌ {code} - 仍然存在（应已删除）")
                all_pass = False
            else:
                print(f"  ✅ {code} - 已清除")
        
        return all_pass

def test_cn_index_data_depth():
    """测试3: 验证 CN 指数历史数据深度（新增）"""
    print("\n" + "="*60)
    print("测试3: CN 指数历史数据深度验证")
    print("="*60)
    
    cn_indices = {
        'CN:INDEX:000001': ('上证综指', 6000),
        'CN:INDEX:000300': ('沪深300', 5000),
        'CN:INDEX:000016': ('上证50', 5000),   # 之前仅1条
        'CN:INDEX:000905': ('中证500', 5000),  # 之前仅1条
    }
    
    with Session(engine) as session:
        all_pass = True
        for symbol, (name, min_records) in cn_indices.items():
            count = session.exec(
                select(func.count(MarketDataDaily.id)).where(
                    MarketDataDaily.symbol == symbol
                )
            ).one()
            
            status = "✅" if count >= min_records else "❌"
            print(f"{status} {name} ({symbol}): {count} 条记录 (要求 >= {min_records})")
            if count < min_records:
                all_pass = False
        
        return all_pass

def test_market_data_depth():
    """测试4: 验证行情数据深度"""
    print("\n" + "="*60)
    print("测试4: 行情数据深度验证")
    print("="*60)
    
    depth_requirements = {
        'US:INDEX:SPX': 5000,
        'CN:INDEX:000001': 6000,
        'US:STOCK:AAPL': 8000,
        'HK:INDEX:HSCC': 3000,  # 使用新代码
        'HK:INDEX:HSCE': 7000,  # 使用新代码
    }
    
    with Session(engine) as session:
        all_pass = True
        for symbol, min_records in depth_requirements.items():
            count = session.exec(
                select(func.count(MarketDataDaily.id)).where(
                    MarketDataDaily.symbol == symbol
                )
            ).one()
            
            status = "✅" if count >= min_records else "❌"
            print(f"{status} {symbol}: {count} 条记录 (要求 >= {min_records})")
            if count < min_records:
                all_pass = False
        
        return all_pass

def test_financial_data_completeness():
    """测试5: 验证财报数据完整性"""
    print("\n" + "="*60)
    print("测试5: 财报数据完整性验证")
    print("="*60)
    
    stock_symbols = [
        'CN:STOCK:600030',
        'CN:STOCK:601998',
        'US:STOCK:AAPL',
        'HK:STOCK:00700',
    ]
    
    with Session(engine) as session:
        all_pass = True
        for symbol in stock_symbols:
            count = session.exec(
                select(func.count(FinancialFundamentals.id)).where(
                    FinancialFundamentals.symbol == symbol
                )
            ).one()
            
            status = "✅" if count >= 3 else "⚠️"
            print(f"{status} {symbol}: {count} 条财报记录")
            if count < 3:
                all_pass = False
        
        return all_pass

def test_valuation_metrics():
    """测试6: 验证估值指标 (PE/PB)"""
    print("\n" + "="*60)
    print("测试6: 估值指标 (PE/PB) 验证")
    print("="*60)
    
    with Session(engine) as session:
        total_stock_records = session.exec(
            select(func.count(MarketDataDaily.id)).where(
                MarketDataDaily.symbol.like('%:STOCK:%')
            )
        ).one()
        
        pe_filled_records = session.exec(
            select(func.count(MarketDataDaily.id)).where(
                MarketDataDaily.symbol.like('%:STOCK:%'),
                MarketDataDaily.pe != None
            )
        ).one()
        
        fill_rate = (pe_filled_records / total_stock_records * 100) if total_stock_records > 0 else 0
        
        status = "✅" if fill_rate > 20 else "⚠️"
        print(f"{status} 个股 PE 填充率: {fill_rate:.1f}% ({pe_filled_records}/{total_stock_records})")
        
        return fill_rate > 20

def test_index_price_sanity():
    """测试7: 验证指数价格合理性"""
    print("\n" + "="*60)
    print("测试7: 指数价格合理性验证")
    print("="*60)
    
    price_checks = {
        'CN:INDEX:000001': (2000, 4000),
        'CN:INDEX:000016': (1500, 4000),  # 新增：上证50
        'CN:INDEX:000905': (3000, 8000),  # 新增：中证500
        'US:INDEX:SPX': (3000, 7000),
        'HK:INDEX:HSI': (10000, 30000),
        'HK:INDEX:HSCC': (2000, 6000),    # 使用新代码
        'HK:INDEX:HSCE': (5000, 15000),   # 使用新代码
    }
    
    with Session(engine) as session:
        all_pass = True
        for symbol, (min_price, max_price) in price_checks.items():
            latest = session.exec(
                select(MarketDataDaily).where(
                    MarketDataDaily.symbol == symbol
                ).order_by(MarketDataDaily.timestamp.desc()).limit(1)
            ).first()
            
            if latest and latest.close:
                in_range = min_price <= latest.close <= max_price
                status = "✅" if in_range else "❌"
                print(f"{status} {symbol}: {latest.close:.2f} (预期 {min_price}-{max_price})")
                if not in_range:
                    all_pass = False
            else:
                print(f"⚠️ {symbol}: 无最新数据")
                all_pass = False
        
        return all_pass

def test_etf_type_recognition():
    """测试8: 验证 ETF 类型识别正确性"""
    print("\n" + "="*60)
    print("测试8: ETF 类型识别验证")
    print("="*60)
    
    etf_assets = {
        'TLT': 'US:ETF:TLT',
        'SPY': 'US:ETF:SPY',
        'QQQ': 'US:ETF:QQQ',
        '159662': 'CN:ETF:159662',
        '512800': 'CN:ETF:512800',
        '02800': 'HK:ETF:02800',
        '03033': 'HK:ETF:03033',
    }
    
    with Session(engine) as session:
        all_pass = True
        for code, expected_id in etf_assets.items():
            item = session.exec(
                select(Watchlist).where(Watchlist.symbol == expected_id)
            ).first()
            
            if item:
                is_etf = ':ETF:' in item.symbol
                status = "✅" if is_etf else "❌"
                print(f"{status} [{code}] -> {item.symbol} ({'ETF' if is_etf else 'WRONG TYPE'})")
                if not is_etf:
                    all_pass = False
            else:
                print(f"❌ [{code}] -> 未找到 {expected_id}")
                all_pass = False
        
        return all_pass

def run_all_tests():
    """运行所有测试"""
    print("\n" + "🧪 开始数据下载完整性验证测试套件 v2.0")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        'ID格式': test_id_format_correctness(),
        'HK指数规范化': test_hk_index_code_normalization(),
        'CN指数数据深度': test_cn_index_data_depth(),
        '行情数据深度': test_market_data_depth(),
        '财报完整性': test_financial_data_completeness(),
        '估值指标': test_valuation_metrics(),
        '价格合理性': test_index_price_sanity(),
        'ETF识别': test_etf_type_recognition(),
    }
    
    print("\n" + "="*60)
    print("📊 测试结果汇总")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    print("\n" + "="*60)
    if all_passed:
        print("🎉 所有测试通过！数据下载质量达标。")
    else:
        print("⚠️ 部分测试未通过，请检查上述失败项。")
    print("="*60)

if __name__ == "__main__":
    run_all_tests()
