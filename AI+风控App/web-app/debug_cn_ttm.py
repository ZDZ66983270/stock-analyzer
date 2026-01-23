#!/usr/bin/env python3
"""
调试 A 股累计数据 TTM 计算逻辑
测试中信证券 (600030) 的 TTM 计算
"""
import sys
sys.path.append('backend')
from sqlmodel import Session, select
from backend.database import engine
from backend.models import FinancialFundamentals

symbol = "CN:STOCK:600030"

print("="*80)
print(f"调试 {symbol} 的 TTM 计算逻辑")
print("="*80)

with Session(engine) as session:
    # 获取所有财报数据
    financials = session.exec(
        select(FinancialFundamentals)
        .where(FinancialFundamentals.symbol == symbol)
        .order_by(FinancialFundamentals.as_of_date.desc())
    ).all()
    
    print(f"\n找到 {len(financials)} 条财报记录\n")
    
    # 分类
    quarterly = [f for f in financials if f.report_type == 'quarterly']
    annual = [f for f in financials if f.report_type == 'annual']
    
    print(f"季报: {len(quarterly)} 条")
    print(f"年报: {len(annual)} 条\n")
    
    # 显示最近的季报
    print("最近4个季度:")
    print("-"*80)
    for i, q in enumerate(quarterly[:4]):
        print(f"Q{i+1}: {q.as_of_date}")
        print(f"   净利润: {q.net_income_ttm/1e8:.2f}亿")
        print(f"   EPS: {q.eps_ttm:.2f}")
        print(f"   数据源: {q.data_source}")
        print(f"   币种: {q.currency}")
    
    # 显示最近的年报
    print("\n最近2个年报:")
    print("-"*80)
    for i, a in enumerate(annual[:2]):
        print(f"年报{i+1}: {a.as_of_date}")
        print(f"   净利润: {a.net_income_ttm/1e8:.2f}亿")
        print(f"   EPS: {a.eps_ttm:.2f}")
        print(f"   数据源: {a.data_source}")
    
    # 测试累计数据逻辑
    print("\n" + "="*80)
    print("测试累计数据 TTM 计算")
    print("="*80)
    
    if len(quarterly) >= 4 and len(annual) >= 1:
        latest = quarterly[0]
        
        print(f"\n最新季报: {latest.as_of_date}")
        print(f"   净利润(累计): {latest.net_income_ttm/1e8:.2f}亿")
        print(f"   数据源: {latest.data_source}")
        
        # 检查是否为累计数据
        is_accumulated = 'akshare' in (latest.data_source or '').lower()
        print(f"   是否累计数据: {is_accumulated}")
        
        if is_accumulated:
            # 应用累计数据公式
            curr_year = int(latest.as_of_date[:4])
            prev_year = curr_year - 1
            target_prev_date = f"{prev_year}{latest.as_of_date[4:]}"
            
            print(f"\n累计数据公式:")
            print(f"   当前年份: {curr_year}")
            print(f"   上一年份: {prev_year}")
            print(f"   目标上年同期日期: {target_prev_date}")
            
            # 查找上年年报
            prev_annual = next((f for f in annual if f.as_of_date.startswith(str(prev_year))), None)
            if prev_annual:
                print(f"\n   ✅ 找到上年年报: {prev_annual.as_of_date}")
                print(f"      净利润: {prev_annual.net_income_ttm/1e8:.2f}亿")
            else:
                print(f"\n   ❌ 未找到上年年报")
            
            # 查找上年同期季报
            prev_same_period = next((f for f in quarterly if f.as_of_date == target_prev_date), None)
            if prev_same_period:
                print(f"\n   ✅ 找到上年同期季报: {prev_same_period.as_of_date}")
                print(f"      净利润(累计): {prev_same_period.net_income_ttm/1e8:.2f}亿")
            else:
                print(f"\n   ❌ 未找到上年同期季报")
                print(f"      可用的季报日期: {[q.as_of_date for q in quarterly]}")
            
            # 计算 TTM
            if prev_annual and prev_same_period:
                remaining = prev_annual.net_income_ttm - prev_same_period.net_income_ttm
                ttm_income = latest.net_income_ttm + remaining
                
                print(f"\n   📊 TTM 计算:")
                print(f"      最新累计值: {latest.net_income_ttm/1e8:.2f}亿")
                print(f"      上年年报: {prev_annual.net_income_ttm/1e8:.2f}亿")
                print(f"      上年同期累计: {prev_same_period.net_income_ttm/1e8:.2f}亿")
                print(f"      上年剩余部分: {remaining/1e8:.2f}亿")
                print(f"      ✅ TTM 净利润 = {latest.net_income_ttm/1e8:.2f} + {remaining/1e8:.2f} = {ttm_income/1e8:.2f}亿")
                
                # 对比 Yahoo Finance
                print(f"\n   对比:")
                print(f"      Yahoo Finance TTM EPS: 1.83")
                print(f"      如果用错误的直接相加:")
                wrong_sum = sum(q.net_income_ttm for q in quarterly[:4]) / 1e8
                print(f"         错误 TTM = {wrong_sum:.2f}亿 (直接相加4个季度)")
            else:
                print(f"\n   ❌ 无法计算 TTM（缺少必要数据）")
        else:
            # 离散数据，直接相加
            print(f"\n   使用离散数据逻辑（直接相加4个季度）")
            ttm_income = sum(q.net_income_ttm for q in quarterly[:4])
            print(f"   TTM 净利润: {ttm_income/1e8:.2f}亿")

print("\n" + "="*80)
print("调试完成")
print("="*80)
