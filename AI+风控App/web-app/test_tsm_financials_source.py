#!/usr/bin/env python3
"""
测试程序：检查美股财报数据源
查询 TSM (台积电) 的最新财报日期
"""
import sys
sys.path.insert(0, '.')

from sqlmodel import Session, select
from backend.database import engine
from backend.models import FinancialFundamentals

def check_tsm_financials():
    print("=" * 60)
    print("检查 TSM (台积电) 财报数据源")
    print("=" * 60)
    
    with Session(engine) as session:
        # 查询 TSM 的所有财报记录
        stmt = select(FinancialFundamentals).where(
            FinancialFundamentals.symbol.like('%TSM%')
        ).order_by(FinancialFundamentals.as_of_date.desc())
        
        results = session.exec(stmt).all()
        
        if not results:
            print("❌ 未找到 TSM 的财报数据")
            return
        
        print(f"\n✅ 找到 {len(results)} 条 TSM 财报记录\n")
        
        # 显示最新的 5 条记录
        print("最新的 5 条财报记录：")
        print("-" * 60)
        for i, record in enumerate(results[:5], 1):
            print(f"\n[{i}] 财报日期: {record.as_of_date}")
            print(f"    Symbol: {record.symbol}")
            print(f"    报告类型: {record.report_type}")
            print(f"    数据源: {record.data_source}")
            print(f"    币种: {record.currency}")
            if record.revenue_ttm:
                print(f"    营收 TTM: {record.revenue_ttm:,.0f}")
            if record.net_income_ttm:
                print(f"    净利润 TTM: {record.net_income_ttm:,.0f}")
            if record.eps:
                print(f"    EPS: {record.eps:.4f}")
        
        # 统计数据源分布
        print("\n" + "=" * 60)
        print("数据源统计：")
        print("-" * 60)
        source_counts = {}
        for record in results:
            source = record.data_source or 'Unknown'
            source_counts[source] = source_counts.get(source, 0) + 1
        
        for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {source}: {count} 条记录")
        
        # 最新财报日期
        latest = results[0]
        print("\n" + "=" * 60)
        print(f"📅 最新财报日期: {latest.as_of_date}")
        print(f"📊 数据源: {latest.data_source}")
        print(f"📋 报告类型: {latest.report_type}")
        print("=" * 60)

if __name__ == "__main__":
    check_tsm_financials()
