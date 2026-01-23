#!/usr/bin/env python3
"""
测试回填脚本对中信证券的 TTM 计算
模拟 backfill_valuation_history.py 的逻辑
"""
import sys
sys.path.append('backend')
from sqlmodel import Session, select
from backend.database import engine
from backend.models import FinancialFundamentals, MarketDataDaily

symbol = "CN:STOCK:600030"
test_date = "2026-01-06"  # 使用最新的日线数据日期

print("="*80)
print(f"测试回填脚本的 TTM 计算逻辑")
print(f"股票: {symbol}, 测试日期: {test_date}")
print("="*80)

with Session(engine) as session:
    # 1. 获取财报数据（按日期降序）
    financials = session.exec(
        select(FinancialFundamentals)
        .where(FinancialFundamentals.symbol == symbol)
        .order_by(FinancialFundamentals.as_of_date.asc())  # 注意：这里是升序
    ).all()
    
    financials_desc = sorted(financials, key=lambda x: x.as_of_date, reverse=True)
    
    print(f"\n加载了 {len(financials)} 条财报")
    
    # 2. 模拟 get_ttm_net_income 函数
    def get_ttm_net_income(target_date):
        valid_fins = [f for f in financials_desc if f.as_of_date <= target_date]
        if not valid_fins:
            return None, None
        
        latest = valid_fins[0]
        
        print(f"\n目标日期: {target_date}")
        print(f"最新财报: {latest.as_of_date} ({latest.report_type})")
        
        # Strategy 1: Quarterly Logic
        if latest.report_type == 'quarterly':
            qs = [f for f in valid_fins if f.report_type == 'quarterly']
            annuals = [f for f in valid_fins if f.report_type == 'annual']
            
            print(f"可用季报: {len(qs)} 条")
            print(f"可用年报: {len(annuals)} 条")
            
            # Check for AkShare Accumulated Data Pattern
            is_accumulated = 'akshare' in (latest.data_source or '').lower()
            print(f"是否累计数据: {is_accumulated}")
            print(f"数据源: {latest.data_source}")
            
            if is_accumulated:
                print(f"\n执行累计数据逻辑...")
                try:
                    curr_year = int(latest.as_of_date[:4])
                    prev_year = curr_year - 1
                    target_prev_date = f"{prev_year}{latest.as_of_date[4:]}"
                    
                    print(f"  当前年份: {curr_year}")
                    print(f"  目标上年同期: {target_prev_date}")
                    
                    prev_annual = next((f for f in annuals if f.as_of_date.startswith(str(prev_year))), None)
                    prev_same_period = next((f for f in qs if f.as_of_date == target_prev_date), None)
                    
                    if prev_annual:
                        print(f"  ✅ 找到上年年报: {prev_annual.as_of_date}")
                    else:
                        print(f"  ❌ 未找到上年年报")
                    
                    if prev_same_period:
                        print(f"  ✅ 找到上年同期: {prev_same_period.as_of_date}")
                    else:
                        print(f"  ❌ 未找到上年同期")
                    
                    if prev_annual and prev_same_period and prev_annual.net_income_ttm and prev_same_period.net_income_ttm:
                        remaining_prev_year = prev_annual.net_income_ttm - prev_same_period.net_income_ttm
                        ttm_val = latest.net_income_ttm + remaining_prev_year
                        
                        print(f"\n  ✅ 累计数据公式计算成功:")
                        print(f"     最新累计: {latest.net_income_ttm/1e8:.2f}亿")
                        print(f"     上年剩余: {remaining_prev_year/1e8:.2f}亿")
                        print(f"     TTM: {ttm_val/1e8:.2f}亿")
                        
                        return ttm_val, latest.currency
                    else:
                        print(f"\n  ⚠️ 累计数据公式失败，回退到直接相加")
                except Exception as e:
                    print(f"\n  ❌ 累计数据逻辑异常: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Fallback (Discrete Summation)
            print(f"\n执行离散数据逻辑（直接相加）...")
            qs_top4 = qs[:4]
            print(f"  取最近 {len(qs_top4)} 个季度")
            
            if len(qs_top4) == 4:
                currencies = {q.currency for q in qs_top4}
                if len(currencies) == 1:
                    total_inc = sum(q.net_income_ttm for q in qs_top4 if q.net_income_ttm)
                    print(f"  ✅ 直接相加 TTM: {total_inc/1e8:.2f}亿")
                    return total_inc, latest.currency
                else:
                    print(f"  ❌ 币种不一致: {currencies}")
            else:
                print(f"  ❌ 季度数量不足4个")
        
        # Strategy 2: Annual Fallback
        print(f"\n回退到年报数据...")
        latest_annual = next((f for f in valid_fins if f.report_type == 'annual'), None)
        if latest_annual:
            print(f"  ✅ 使用年报: {latest_annual.as_of_date}, {latest_annual.net_income_ttm/1e8:.2f}亿")
            return latest_annual.net_income_ttm, latest_annual.currency
        
        print(f"  ❌ 无可用数据")
        return None, None
    
    # 3. 测试
    ttm_income, currency = get_ttm_net_income(test_date)
    
    if ttm_income:
        print(f"\n" + "="*80)
        print(f"最终结果:")
        print(f"  TTM 净利润: {ttm_income/1e8:.2f}亿 {currency}")
        print(f"="*80)
    else:
        print(f"\n❌ 无法计算 TTM")
