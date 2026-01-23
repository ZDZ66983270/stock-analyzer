#!/usr/bin/env python3
"""
最终版数据质量测试套件 (Test Suite: Final Data Quality)
覆盖：
1. ID 格式规范 (HK指数无0前缀, Crypto使用CODE-USD)
2. 关键资产数据深度 (包括上证50, 中证500)
3. 资产类型识别 (ETF正确性)
4. 价格合理性 (防止数量级错误)
5. 财报完整性
6. 估值指标填充
"""
import sys
import os
from datetime import datetime

sys.path.append(os.path.join(os.getcwd(), 'backend'))
from database import engine
from sqlmodel import Session, select, func
from models import Watchlist, Index, MarketDataDaily, FinancialFundamentals, MarketSnapshot

def run_test(name, check_func, session):
    """运行单个测试并打印结果"""
    print(f"\n🧪 测试: {name}")
    print("-" * 60)
    try:
        passed = check_func(session)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"结果: {status}")
        return passed
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

# ==========================================
# 1. 标识符规范测试
# ==========================================

def check_id_normalization(session):
    """验证 ID 规范性：HK指数无0前缀，Crypto格式正确"""
    all_pass = True
    
    # 1. HK 指数检查 (必须是 HSCC/HSCE, 不能是 0HSCC/0HSCE)
    hk_indices = {
        'HK:INDEX:HSCC': '红筹指数',
        'HK:INDEX:HSCE': '国企指数',
        'HK:INDEX:HSI': '恒生指数'
    }
    forbidden_hk = ['HK:INDEX:0HSCC', 'HK:INDEX:0HSCE']
    
    print("  [HK 指数规范性]")
    for code, name in hk_indices.items():
        exists = session.exec(select(Index).where(Index.symbol == code)).first()
        if exists:
            print(f"    ✅ {code} ({name}) - 存在")
        else:
            print(f"    ❌ {code} ({name}) - 缺失")
            all_pass = False
            
    for code in forbidden_hk:
        exists = session.exec(select(Index).where(Index.symbol == code)).first()
        if exists:
            print(f"    ❌ {code} - 仍然存在 (应删除)")
            all_pass = False
        else:
            print(f"    ✅ {code} - 已清除")

    # 2. Crypto 格式检查 (必须是 CRYPTO:CODE-USD)
    print("\n  [Crypto 格式规范性]")
    # 检查是否有 CRYPTO:STOCK:BTC 这种旧格式
    old_crypto = session.exec(select(Watchlist).where(Watchlist.symbol.like('CRYPTO:STOCK:%'))).all()
    if old_crypto:
        print(f"    ❌ 发现 {len(old_crypto)} 个旧格式 Crypto ID (e.g. {old_crypto[0].symbol})")
        all_pass = False
    else:
        print("    ✅ 旧格式 Crypto ID 已清除")
        
    # 检查 BTC 是否为 CRYPTO:BTC-USD
    btc = session.exec(select(Watchlist).where(Watchlist.symbol == 'CRYPTO:BTC-USD')).first()
    if btc:
        print("    ✅ CRYPTO:BTC-USD - 存在")
    else:
        # 尝试查找其他 BTC
        btc_alt = session.exec(select(Watchlist).where(Watchlist.symbol.contains('BTC'))).first()
        print(f"    ℹ️ BTC 当前状态: {btc_alt.symbol if btc_alt else '未找到'}")
        if not btc_alt or btc_alt.symbol != 'CRYPTO:BTC-USD':
            all_pass = False

    return all_pass

def check_etf_recognition(session):
    """验证 ETF 类型识别"""
    etf_assets = {
        'TLT': 'US:ETF:TLT',
        'SPY': 'US:ETF:SPY',
        '159662': 'CN:ETF:159662', # A股 ETF
        '512800': 'CN:ETF:512800', # A股 ETF
        '02800': 'HK:ETF:02800',   # 港股 ETF
    }
    
    all_pass = True
    for name, expected_id in etf_assets.items():
        item = session.exec(select(Watchlist).where(Watchlist.symbol == expected_id)).first()
        if item:
            is_etf = ':ETF:' in item.symbol
            status = "✅" if is_etf else "❌"
            print(f"    {status} {name} -> {item.symbol} ({'ETF' if is_etf else 'WRONG TYPE'})")
            if not is_etf: all_pass = False
        else:
            print(f"    ❌ {name} -> 未找到 {expected_id}")
            all_pass = False
    return all_pass

# ==========================================
# 2. 数据深度与完整性测试
# ==========================================

def check_data_depth(session):
    """验证关键资产的历史数据深度"""
    targets = {
        'CN:INDEX:000001': ('上证综指', 6000),
        'CN:INDEX:000016': ('上证50', 5000),   # 曾有缺失问题
        'CN:INDEX:000905': ('中证500', 5000),  # 曾有缺失问题
        'US:INDEX:SPX': ('标普500', 5000),
        'HK:INDEX:HSI': ('恒生指数', 8000),
        'US:ETF:TLT': ('TLT', 5000)
    }
    
    all_pass = True
    for symbol, (name, min_count) in targets.items():
        count = session.exec(select(func.count(MarketDataDaily.id)).where(MarketDataDaily.symbol == symbol)).one()
        status = "✅" if count >= min_count else "❌"
        print(f"    {status} {name:<8} ({symbol}): {count:>5} 条 (要求 >={min_count})")
        if count < min_count: all_pass = False
    return all_pass

def check_financials(session):
    """验证财报数据是否存在"""
    targets = ['CN:STOCK:600030', 'US:STOCK:AAPL', 'HK:STOCK:00700']
    all_pass = True
    for symbol in targets:
        count = session.exec(select(func.count(FinancialFundamentals.id)).where(FinancialFundamentals.symbol == symbol)).one()
        status = "✅" if count >= 3 else "⚠️"
        print(f"    {status} {symbol}: {count} 条财报")
        if count < 3: all_pass = False
    return all_pass

# ==========================================
# 3. 业务逻辑与合理性测试
# ==========================================

def check_price_reasonability(session):
    """验证价格在合理区间 (防止单位错误)"""
    checks = {
        'CN:INDEX:000001': (2000, 4000),  # 上证不在 3000 以下太远
        'HK:INDEX:HSI': (10000, 35000),
        'US:INDEX:SPX': (3000, 8000),
        'CN:INDEX:000905': (3000, 8000), # 中证500
    }
    all_pass = True
    for symbol, (min_p, max_p) in checks.items():
        latest = session.exec(select(MarketDataDaily).where(MarketDataDaily.symbol == symbol).order_by(MarketDataDaily.timestamp.desc()).limit(1)).first()
        if latest:
            price = latest.close
            ok = min_p <= price <= max_p
            status = "✅" if ok else "❌"
            print(f"    {status} {symbol}: {price:.2f} (区间 {min_p}-{max_p})")
            if not ok: all_pass = False
        else:
            print(f"    ❌ {symbol}: 无数据")
            all_pass = False
    return all_pass

def check_valuation_metrics(session):
    """验证 PE/PB 填充率"""
    total = session.exec(select(func.count(MarketDataDaily.id)).where(MarketDataDaily.symbol.like('%:STOCK:%'))).one()
    filled = session.exec(select(func.count(MarketDataDaily.id)).where(MarketDataDaily.symbol.like('%:STOCK:%'), MarketDataDaily.pe != None)).one()
    
    if total == 0:
        print("    ⚠️ 无股票数据")
        return False
        
    rate = (filled / total) * 100
    status = "✅" if rate > 20 else "⚠️"  # 20% 是基准线 (考虑到早期数据无财报)
    print(f"    {status} 个股 PE 填充率: {rate:.1f}% ({filled}/{total})")
    
    return rate > 20

# ==========================================
# 主程序
# ==========================================

def main():
    print("\n" + "="*60)
    print("📊 最终数据质量验收测试 (Final Acceptance Test)")
    print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    results = {}
    with Session(engine) as session:
        results['ID规范性'] = run_test("ID 规范化 (HK/Crypto)", check_id_normalization, session)
        results['ETF识别'] = run_test("ETF 类型识别", check_etf_recognition, session)
        results['数据深度'] = run_test("关键资产数据深度", check_data_depth, session)
        results['价格合理性'] = run_test("价格合理性验证", check_price_reasonability, session)
        results['财报完整性'] = run_test("财报数据完整性", check_financials, session)
        results['估值指标'] = run_test("估值指标 (PE/PB) 覆盖", check_valuation_metrics, session)

    print("\n" + "="*60)
    print("🏆 测试结果汇总")
    print("="*60)
    all_passed = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:<15} : {status}")
        if not passed: all_passed = False
    
    print("-" * 60)
    if all_passed:
        print("✨ 系统数据质量：优异 (Ready for Production)")
    else:
        print("⚠️ 系统数据质量：存在瑕疵 (请检查失败项)")
    print("="*60)

if __name__ == "__main__":
    main()
