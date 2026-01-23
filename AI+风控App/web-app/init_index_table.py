"""
初始化Index表并填充三大市场的指数数据
"""
import sys
sys.path.insert(0, 'backend')

from database import create_db_and_tables, engine
from models import Index
from sqlmodel import Session, select

# 三大市场的指数配置
INDICES = [
    # 美股指数
    {"symbol": "DJI", "name": "道琼斯工业平均指数", "market": "US"},
    {"symbol": "NDX", "name": "纳斯达克100指数", "market": "US"},
    {"symbol": "SPX", "name": "标普500指数", "market": "US"},
    
    # 港股指数
    {"symbol": "HSI", "name": "恒生指数", "market": "HK"},
    {"symbol": "HSTECH", "name": "恒生科技指数", "market": "HK"},
    
    # A股指数
    {"symbol": "000001", "name": "上证综合指数", "market": "CN"},
]

print("="*60)
print("初始化Index表")
print("="*60)

# 1. 确保表已创建
print("\n1. 创建数据库表...")
create_db_and_tables()
print("   ✅ 表创建完成")

# 2. 填充指数数据
print("\n2. 填充指数数据...")
from symbol_utils import get_canonical_id

with Session(engine) as session:
    added_count = 0
    updated_count = 0
    
    for idx_config in INDICES:
        raw_symbol = idx_config["symbol"]
        name = idx_config["name"]
        market = idx_config["market"]
        
        # 构造典范 ID
        symbol, _ = get_canonical_id(raw_symbol, market, 'INDEX')
        
        # 检查是否已存在
        existing = session.exec(
            select(Index).where(Index.symbol == symbol)
        ).first()
        
        if existing:
            # 更新名称（如果有变化）
            if existing.name != name or existing.market != market:
                existing.name = name
                existing.market = market
                session.add(existing)
                updated_count += 1
                print(f"   🔄 更新: {symbol} - {name}")
            else:
                print(f"   ⏭️  跳过: {symbol} - {name} (已存在)")
        else:
            # 添加新指数
            new_index = Index(
                symbol=symbol,
                name=name,
                market=market
            )
            session.add(new_index)
            added_count += 1
            print(f"   ✅ 添加: {symbol} - {name}")
    
    session.commit()

print("\n" + "="*60)
print("初始化完成")
print("="*60)
print(f"✅ 新增: {added_count} 个指数")
print(f"🔄 更新: {updated_count} 个指数")

# 3. 验证结果
print("\n3. 验证Index表...")
with Session(engine) as session:
    all_indices = session.exec(select(Index)).all()
    print(f"   总计: {len(all_indices)} 个指数")
    print("\n   指数列表:")
    for idx in all_indices:
        print(f"      - {idx.symbol} ({idx.market}): {idx.name}")

print("\n🎉 Index表初始化成功！")
