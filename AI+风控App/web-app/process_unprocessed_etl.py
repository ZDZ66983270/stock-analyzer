"""
批量处理所有未经过ETL的RawMarketData数据
"""
import sys
sys.path.insert(0, 'backend')

from etl_service import ETLService
from database import engine
from sqlmodel import Session, select
from models import RawMarketData

print("🔄 开始批量处理未经过ETL的数据...")

with Session(engine) as session:
    # 查询所有未处理的数据
    unprocessed = session.exec(
        select(RawMarketData).where(RawMarketData.processed == 0)
    ).all()
    
    total = len(unprocessed)
    print(f"\n📊 找到 {total} 条未处理记录")
    
    if total == 0:
        print("✅ 所有数据都已处理！")
        sys.exit(0)
    
    # 按symbol分组统计
    from collections import defaultdict
    by_symbol = defaultdict(int)
    for record in unprocessed:
        by_symbol[f"{record.symbol} ({record.market})"] += 1
    
    print("\n📋 未处理数据统计:")
    for symbol, count in sorted(by_symbol.items()):
        print(f"   - {symbol}: {count}条")
    
    # 批量处理
    print(f"\n🚀 开始处理...")
    success_count = 0
    fail_count = 0
    failed_items = []
    
    for idx, record in enumerate(unprocessed, 1):
        try:
            print(f"[{idx}/{total}] 处理 {record.symbol} (ID: {record.id})...", end=" ")
            ETLService.process_raw_data(record.id)
            print("✅")
            success_count += 1
        except Exception as e:
            print(f"❌ {str(e)[:50]}")
            fail_count += 1
            failed_items.append(f"{record.symbol} (ID: {record.id})")
    
    # 总结
    print("\n" + "="*60)
    print("📊 处理完成统计")
    print("="*60)
    print(f"✅ 成功: {success_count} 条")
    print(f"❌ 失败: {fail_count} 条")
    
    if failed_items:
        print(f"\n⚠️  失败列表:")
        for item in failed_items:
            print(f"   - {item}")
    
    print("\n🎉 批量ETL处理完成！")
