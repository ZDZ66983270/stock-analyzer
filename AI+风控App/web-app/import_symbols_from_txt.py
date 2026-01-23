#!/usr/bin/env python3
"""
从 symbols.txt 导入资产到 Watchlist 和 Index 表
"""
import sys
sys.path.append('backend')

from pathlib import Path
from sqlmodel import Session, select
from backend.database import engine
from backend.models import Watchlist
from backend.symbol_utils import get_canonical_id
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ImportSymbols")


def import_symbols_to_tables():
    """从 symbols.txt 导入资产列表到 watchlist 和 index 表"""
    print(f"\n{'='*80}")
    print(f"📥 从 symbols.txt 导入资产列表")
    print(f"{'='*80}\n")
    
    symbols_file = Path("imports/symbols.txt")
    
    if not symbols_file.exists():
        logger.error(f"  ❌ {symbols_file} 不存在")
        return
    
    with Session(engine) as session:
        # 读取 symbols.txt
        with open(symbols_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 解析注释确定当前分类
        current_market = None
        current_type = None
        added_watchlist = 0
        added_index = 0
        
        # 注释模式映射
        section_patterns = {
            'A股指数 (CN Indices)': ('CN', 'INDEX'),
            '港股指数 (HK Indices)': ('HK', 'INDEX'),
            '美股指数 (US Indices)': ('US', 'INDEX'),
            'A股 (CN Stocks)': ('CN', 'STOCK'),
            'A股 ETF (CN ETFs)': ('CN', 'ETF'),
            '港股 (HK Stocks)': ('HK', 'STOCK'),
            '港股 ETF (HK ETFs)': ('HK', 'ETF'),
            '美股 (US Stocks)': ('US', 'STOCK'),
            '美股 ETF (US ETFs)': ('US', 'ETF'),
            '信托基金 (Trusts)': ('US', 'UTRUST'),
            '加密货币 (Crypto)': ('CRYPTO', 'CRYPTO'),
        }
        
        for line in lines:
            line = line.strip()
            
            # 检查是否是分类注释
            if line.startswith('#'):
                for pattern, (market, asset_type) in section_patterns.items():
                    if pattern in line:
                        current_market = market
                        current_type = asset_type
                        logger.info(f"\n📂 进入分类: {pattern}")
                        break
                continue
            
            # 跳过空行
            if not line:
                continue
            
            # 如果没有设置当前分类，跳过
            if current_type is None:
                continue
            
            code = line.split()[0]  # 只取第一个部分
            
            try:
                # 对于指数，需要根据代码判断市场
                if current_type == 'INDEX':
                    if code.isdigit() and len(code) == 6:
                        market = 'CN'
                    elif code in ['HSI', 'HSTECH', 'HSCC', 'HSCE']:
                        market = 'HK'
                    else:
                        market = 'US'
                else:
                    market = current_market
                
                # 获取典范 ID
                canonical_id, canonical_market = get_canonical_id(code, market, current_type)
                
                # 统一添加到 Watchlist 表
                existing = session.exec(
                    select(Watchlist).where(Watchlist.symbol == canonical_id)
                ).first()
                
                if existing:
                    logger.info(f"  ⏭️  {canonical_id} 已存在于 Watchlist")
                else:
                    new_item = Watchlist(
                        symbol=canonical_id,
                        market=canonical_market,
                        name=code # Ideally fetch name, but here use code as placeholder
                    )
                    session.add(new_item)
                    added_watchlist += 1
                    logger.info(f"  ✅ Watchlist: {code} → {canonical_id} ({canonical_market}, {current_type})")
                
            except Exception as e:
                logger.error(f"  ❌ 处理 {code} 失败: {e}")
                continue
        
        session.commit()
        
        print(f"\n{'='*80}")
        print(f"✅ 导入完成!")
        print(f"{'='*80}")
        print(f"  - Watchlist 新增: {added_watchlist} 个")
        print(f"{'='*80}\n")
        
        # 显示导入结果
        print("📋 Watchlist 表:")
        watchlist_items = session.exec(select(Watchlist).order_by(Watchlist.market, Watchlist.symbol)).all()
        for w in watchlist_items:
            print(f"  {w.symbol:<25} | {w.name:<15} | {w.market}")
        
        print(f"\n总计: Watchlist={len(watchlist_items)}")


if __name__ == "__main__":
    import_symbols_to_tables()
