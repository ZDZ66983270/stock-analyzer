#!/usr/bin/env python3
"""
迁移财报数据的symbol格式从纯代码到Canonical ID
同时清理fetch_financials.py中的调用逻辑
"""
import sys
sys.path.append('backend')

from sqlmodel import Session, select
from backend.database import engine
from backend.models import FinancialFundamentals

def migrate_financial_symbols():
    """将财报数据的symbol从纯代码迁移到Canonical ID"""
    print("=" * 80)
    print("迁移财报数据Symbol格式")
    print("=" * 80)
    
     with Session(engine) as session:
        from sqlalchemy import func
        
        # 1. 更新港股 (00700 -> HK:STOCK:00700)
        hk_records = session.exec(
            select(FinancialFundamentals).where(
                FinancialFundamentals.symbol.notlike('%:%'),  # 不包含冒号
                FinancialFundamentals.symbol.like('0%'),  # 以0开头
                func.length(FinancialFundamentals.symbol) == 5  # 长度为5
            )
        ).all()
        
        print(f"\n📊 港股记录: {len(hk_records)}条")
        for record in hk_records:
            old_symbol = record.symbol
            record.symbol = f"HK:STOCK:{old_symbol}"
            print(f"  {old_symbol} -> {record.symbol}")
        
        # 2. 更新美股 (AAPL -> US:STOCK:AAPL)
        # 查询所有不包含冒号且不以0开头的记录
        us_records = session.exec(
            select(FinancialFundamentals).where(
                FinancialFundamentals.symbol.notlike('%:%'),  # 不包含冒号
                FinancialFundamentals.symbol.notlike('0%')  # 不以0开头
            )
        ).all()
        
        print(f"\n📊 美股记录: {len(us_records)}条")
        for record in us_records:
            old_symbol = record.symbol
            record.symbol = f"US:STOCK:{old_symbol}"
            print(f"  {old_symbol} -> {record.symbol}")
        
        # 3. 提交更改
        total_updated = len(hk_records) + len(us_records)
        if total_updated > 0:
            session.commit()
            print(f"\n✅ 成功迁移 {total_updated} 条记录")
        else:
            print(f"\n✅ 所有记录已使用Canonical ID,无需迁移")
    
    print("\n" + "=" * 80)
    print("迁移完成")
    print("=" * 80)

if __name__ == "__main__":
    migrate_financial_symbols()
