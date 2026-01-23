#!/usr/bin/env python3
"""
测试港股季报数据获取
仅针对腾讯 (00700) 进行测试
"""
import sys
sys.path.append('backend')
from sqlmodel import Session
from backend.database import engine
from backend.models import FinancialFundamentals
from sqlalchemy import delete

# 导入修改后的函数
sys.path.insert(0, '.')
from fetch_financials import fetch_akshare_hk_financials

print("="*80)
print("测试港股季报数据获取")
print("="*80)

# 测试股票
test_symbol = "HK:STOCK:00700"

print(f"\n清理 {test_symbol} 的现有财报数据...")
with Session(engine) as session:
    stmt = delete(FinancialFundamentals).where(FinancialFundamentals.symbol == test_symbol)
    result = session.exec(stmt)
    session.commit()
    print(f"✅ 删除了 {result.rowcount} 条记录")

print(f"\n获取 {test_symbol} 的财报数据...")
data_list = fetch_akshare_hk_financials(test_symbol)

print(f"\n获取结果: {len(data_list)} 条记录")

if data_list:
    # 按类型分组
    annual = [d for d in data_list if d['report_type'] == 'annual']
    quarterly = [d for d in data_list if d['report_type'] == 'quarterly']
    
    print(f"\n年报: {len(annual)} 条")
    for d in annual:
        print(f"  {d['as_of_date']}: 净利润 {d['net_income_ttm']/1e9:.2f}亿, EPS {d['eps_ttm']:.2f}")
    
    print(f"\n季报: {len(quarterly)} 条")
    for d in quarterly:
        print(f"  {d['as_of_date']}: 净利润 {d['net_income_ttm']/1e9:.2f}亿, EPS {d['eps_ttm']:.2f}")
    
    # 保存到数据库
    print(f"\n保存到数据库...")
    with Session(engine) as session:
        for d in data_list:
            fin = FinancialFundamentals(**d)
            session.add(fin)
        session.commit()
    print("✅ 保存成功")
    
    # 验证
    print(f"\n验证数据库...")
    with Session(engine) as session:
        from sqlmodel import select
        fins = session.exec(
            select(FinancialFundamentals)
            .where(FinancialFundamentals.symbol == test_symbol)
            .order_by(FinancialFundamentals.as_of_date.desc())
        ).all()
        print(f"✅ 数据库中共有 {len(fins)} 条记录")
        
        # 检查最近4个季度
        quarterly_fins = [f for f in fins if f.report_type == 'quarterly']
        if len(quarterly_fins) >= 4:
            print(f"\n最近4个季度:")
            ttm_income = 0
            ttm_eps = 0
            for f in quarterly_fins[:4]:
                print(f"  {f.as_of_date}: 净利润 {f.net_income_ttm/1e9:.2f}亿, EPS {f.eps_ttm:.2f}")
                ttm_income += f.net_income_ttm
                ttm_eps += f.eps_ttm
            print(f"\n  TTM 净利润: {ttm_income/1e9:.2f}亿")
            print(f"  TTM EPS: {ttm_eps:.2f}")

print("\n" + "="*80)
print("测试完成")
print("="*80)
