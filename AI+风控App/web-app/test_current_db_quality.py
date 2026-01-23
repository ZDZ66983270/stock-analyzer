#!/usr/bin/env python3
"""
当前数据库质量检查 (Current DB Quality Check)
包含:
1. 基础数据质量 (ID, ETF, 深度, 价格, 财报, 估值) - 来自原 test_data_quality_final.py
2. [新增] HK 时间戳规范性 (必须为 16:00:00)
3. [新增] HK 盘中合规性 (Premature Close Check)
"""
import sys
import os
import pandas as pd
from datetime import datetime, time
from sqlmodel import Session, select, func

# 添加后端路径
sys.path.append(os.path.join(os.getcwd(), 'backend'))
if os.path.join(os.getcwd(), 'web-app/backend') not in sys.path:
     sys.path.append(os.path.join(os.getcwd(), 'web-app/backend'))

from database import engine
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
        import traceback
        traceback.print_exc()
        return False

# ==========================================
# 原有测试逻辑 (复用)
# ==========================================

def check_id_normalization(session):
    """验证 ID 规范性"""
    all_pass = True
    hk_indices = {'HK:INDEX:HSI': '恒生指数'} # Simplified
    for code, name in hk_indices.items():
        exists = session.exec(select(Index).where(Index.symbol == code)).first()
        if not exists:
            print(f"    ❌ {code} ({name}) - 缺失")
            all_pass = False
        else:
            print(f"    ✅ {code} - 存在")
    
    # Check forbidden
    if session.exec(select(Index).where(Index.symbol == 'HK:INDEX:0HSI')).first():
         print(f"    ❌ HK:INDEX:0HSI - 仍然存在")
         all_pass = False

    # Check Crypto
    btc = session.exec(select(Watchlist).where(Watchlist.symbol == 'CRYPTO:BTC-USD')).first()
    if btc:
        print("    ✅ CRYPTO:BTC-USD - 存在")
    else:
        print("    ℹ️ CRYPTO:BTC-USD - 未找到") # Not strictly fail if user didn't add it
        
    return all_pass

def check_etf_recognition(session):
    """验证 ETF 类型识别 (抽样)"""
    # Simply check one known ETF if exists
    target = 'US:ETF:TLT'
    item = session.exec(select(Watchlist).where(Watchlist.symbol == target)).first()
    if item:
        is_etf = ':ETF:' in item.symbol
        print(f"    {'✅' if is_etf else '❌'} {target} is ETF? {is_etf}")
        return is_etf
    return True

def check_data_depth(session):
    """验证关键资产深度"""
    targets = ['HK:INDEX:HSI', 'US:INDEX:SPX']
    all_pass = True
    for t in targets:
        count = session.exec(select(func.count(MarketDataDaily.id)).where(MarketDataDaily.symbol == t)).one()
        print(f"    {'✅' if count > 0 else '❌'} {t}: {count} 条")
        if count == 0: all_pass = False
    return all_pass

def check_price_reasonability(session):
    """验证价格合理性"""
    hsi = session.exec(select(MarketDataDaily).where(MarketDataDaily.symbol == 'HK:INDEX:HSI').order_by(MarketDataDaily.timestamp.desc()).limit(1)).first()
    if hsi and 10000 < hsi.close < 35000:
        print(f"    ✅ HSI Price: {hsi.close}")
        return True
    elif hsi:
        print(f"    ❌ HSI Possible Error: {hsi.close}")
        return False
    return True # Skip if no data

def check_financials(session):
    """验证财报"""
    # Check 00700
    count = session.exec(select(func.count(FinancialFundamentals.id)).where(FinancialFundamentals.symbol == 'HK:STOCK:00700')).one()
    print(f"    {'✅' if count >= 3 else '⚠️'} 00700: {count} 条财报")
    return True

def check_valuation_metrics(session):
    """验证估值"""
    # Check simple coverage
    total = session.exec(select(func.count(MarketDataDaily.id)).where(MarketDataDaily.symbol == 'HK:STOCK:00700')).one()
    filled = session.exec(select(func.count(MarketDataDaily.id)).where(MarketDataDaily.symbol == 'HK:STOCK:00700', MarketDataDaily.pe != None)).one()
    if total > 0:
        print(f"    ℹ️ 00700 PE Coverage: {filled}/{total} ({filled/total:.1%})")
    return True

# ==========================================
# [新增] HK 时间戳专项检查
# ==========================================

def check_hk_timestamp_validity(session):
    """
    [新增] 验证 HK 历史日线数据时间戳是否统一为 16:00:00
    抽样检查: HSI, 00700
    """
    targets = ['HK:INDEX:HSI', 'HK:STOCK:00700']
    all_pass = True
    
    for symbol in targets:
        print(f"  检查 {symbol}...")
        # 获取最近 50 条记录
        records = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.symbol == symbol)
            .order_by(MarketDataDaily.timestamp.desc())
            .limit(50)
        ).all()
        
        if not records:
            print(f"    ⚠️ 无数据，跳过")
            continue
            
        error_count = 0
        for r in records:
            # 转换为 datetime 对象 (sqlite存储为字符串或datetime)
            ts = pd.to_datetime(r.timestamp)
            if ts.time() != time(16, 0, 0):
                error_count += 1
                if error_count <= 3: # 仅打印前几个错误
                    print(f"    ❌ 异常时间戳: {ts}")
        
        if error_count == 0:
            print(f"    ✅ 最近 50 条记录时间戳均为 16:00:00")
        else:
            print(f"    ❌ 发现 {error_count} 条异常时间戳 (非 16:00:00)")
            all_pass = False
            
    return all_pass

def check_hk_premature_close(session):
    """
    [新增] 检查是否在未收盘时(当前时间 < 16:00) 出现了今日收盘数据(timestamp == 16:00)
    """
    now = datetime.now()
    market_close_time = time(16, 0, 0)
    
    print(f"  当前系统时间: {now}")
    
    # 只有当现在时间早于今天 16:00 时，这个检查才有意义
    if now.time() >= market_close_time:
        print("  ℹ️ 当前已过 16:00，跳过盘中合规性检查 (Premature Check)。")
        return True
        
    print("  🔒 当前为盘中时间，执行 Premature Check...")
    
    target_date_str = now.strftime('%Y-%m-%d')
    # 构造一种可能的错误 timestamp: "YYYY-MM-DD 16:00:00"
    forbidden_ts = f"{target_date_str} 16:00:00"
    
    # 检查任意 HK 标的
    # 只要发现一条今日 16:00 的数据，就说明有问题
    problem_record = session.exec(
        select(MarketDataDaily)
        .where(MarketDataDaily.market == 'HK')
        .where(MarketDataDaily.timestamp == forbidden_ts)
        .limit(1)
    ).first()
    
    if problem_record:
        print(f"  ❌ 严重错误! 尚未收盘却发现了今日收盘数据:")
        print(f"     Symbol: {problem_record.symbol}")
        print(f"     Timestamp: {problem_record.timestamp}")
        print(f"     -> 这意味着 ETL 错误地将盘中数据标记为了收盘数据。")
        return False
    else:
        print(f"  ✅ 未发现 '{forbidden_ts}' 的未来数据。")
        return True

# ==========================================
# 主程序
# ==========================================

def main():
    print("\n" + "="*60)
    print("🛡️ 增强版数据库质量检查 (含 HK 时间戳校验)")
    print(f"⏰ 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    results = {}
    with Session(engine) as session:
        # 1. 基础检查
        results['ID规范性'] = run_test("ID 规范化", check_id_normalization, session)
        results['关键深度'] = run_test("关键资产深度", check_data_depth, session)
        results['价格合理'] = run_test("价格合理性", check_price_reasonability, session)
        
        # 2. 专项检查
        results['HK时间戳格式'] = run_test("HK 历史时间戳规范 (16:00:00)", check_hk_timestamp_validity, session)
        results['HK盘中合规'] = run_test("HK 盘中合规性 (Premature Check)", check_hk_premature_close, session)
        
    print("\n" + "="*60)
    print("🏆 汇总结果")
    all_passed = True
    for name, passed in results.items():
        print(f"{name:<20}: {'✅ PASS' if passed else '❌ FAIL'}")
        if not passed: all_passed = False
    
    print("-" * 60)
    if all_passed:
        print("✨ 所有检查通过")
    else:
        print("⚠️ 发现潜在问题")
    print("="*60)

if __name__ == "__main__":
    main()
