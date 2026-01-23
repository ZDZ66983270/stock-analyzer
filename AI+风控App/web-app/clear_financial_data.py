#!/usr/bin/env python3
"""清除财务报表数据"""
from sqlmodel import Session
from backend.database import engine
from backend.models import FinancialFundamentals

with Session(engine) as session:
    # 获取所有记录并删除
    all_records = session.query(FinancialFundamentals).all()
    count = len(all_records)
    
    print(f'📊 当前财务报表记录数: {count}')
    
    if count > 0:
        print('🗑️  开始清除财务报表数据...')
        
        for record in all_records:
            session.delete(record)
        
        session.commit()
        
        # 验证
        remaining = session.query(FinancialFundamentals).count()
        print(f'✅ 清除完成！剩余记录数: {remaining}')
    else:
        print('ℹ️  财务报表表已经是空的')
