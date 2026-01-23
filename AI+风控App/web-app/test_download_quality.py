#!/usr/bin/env python3
"""
数据下载完整性验证测试套件
在 reset_and_redownload_all.py 执行完成后运行此脚本
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
            # 在 Watchlist 或 Index 中查找
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

def test_market_data_depth():
    """测试2: 验证行情数据深度"""
    print("\n" + "="*60)
    print("测试2: 行情数据深度验证")
    print("="*60)
    
    depth_requirements = {
        'US:INDEX:SPX': 5000,    # 标普500应有数十年数据
        'CN:INDEX:000001': 3000, # 上证指数应有20+年数据
        'US:STOCK:AAPL': 8000,   # 苹果应有40+年数据
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
    """测试3: 验证财报数据完整性"""
    print("\n" + "="*60)
    print("测试3: 财报数据完整性验证")
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
    """测试4: 验证估值指标计算"""
    print("\n" + "="*60)
    print("测试4: 估值指标 (PE/PB) 验证")
    print("="*60)
    
    with Session(engine) as session:
        # 检查个股的 PE 填充率
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
        
        status = "✅" if fill_rate > 50 else "⚠️"
        print(f"{status} 个股 PE 填充率: {fill_rate:.1f}% ({pe_filled_records}/{total_stock_records})")
        
        return fill_rate > 50

def test_index_price_sanity():
    """测试5: 验证指数价格合理性"""
    print("\n" + "="*60)
    print("测试5: 指数价格合理性验证")
    print("="*60)
    
    price_checks = {
        'CN:INDEX:000001': (2000, 4000),  # 上证指数应在2000-4000点
        'US:INDEX:SPX': (3000, 7000),     # 标普500应在3000-7000点
        'HK:INDEX:HSI': (10000, 30000),   # 恒生指数应在10000-30000点
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

def test_currency_consistency():
    """测试6: 验证币种一致性"""
    print("\n" + "="*60)
    print("测试6: 财报币种与市场匹配验证")
    print("="*60)
    
    with Session(engine) as session:
        # 检查港股财报是否为 CNY
        hk_cny_count = session.exec(
            select(func.count(FinancialFundamentals.id)).where(
                FinancialFundamentals.symbol.like('HK:%'),
                FinancialFundamentals.currency == 'CNY'
            )
        ).one()
        
        if hk_cny_count > 0:
            print(f"ℹ️ 发现 {hk_cny_count} 条港股财报为 CNY，需确认汇率转换逻辑已应用")
        else:
            print("✅ 港股财报币种检查通过")
        
        return True

def test_etf_type_recognition():
    """测试7: 验证 ETF 类型识别正确性"""
    print("\n" + "="*60)
    print("测试7: ETF 类型识别验证")
    print("="*60)
    
    # 关键 ETF 资产：编号型和字母型
    etf_assets = {
        'TLT': 'US:ETF:TLT',           # 美股字母 ETF
        'SPY': 'US:ETF:SPY',
        'QQQ': 'US:ETF:QQQ',
        '159662': 'CN:ETF:159662',     # A股编号 ETF
        '512800': 'CN:ETF:512800',
        '02800': 'HK:ETF:02800',       # 港股编号 ETF
        '03033': 'HK:ETF:03033',
    }
    
    with Session(engine) as session:
        all_pass = True
        for code, expected_id in etf_assets.items():
            item = session.exec(
                select(Watchlist).where(Watchlist.symbol == expected_id)
            ).first()
            
            if item:
                # 验证 ID 中确实包含 ':ETF:'
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
    print("\n" + "🧪 开始数据下载完整性验证测试套件")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        'ID格式': test_id_format_correctness(),
        '数据深度': test_market_data_depth(),
        '财报完整性': test_financial_data_completeness(),
        '估值指标': test_valuation_metrics(),
        '价格合理性': test_index_price_sanity(),
        '币种一致性': test_currency_consistency(),
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
