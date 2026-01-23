#!/usr/bin/env python3
"""
数据库 ID 统一化迁移脚本 (Database Canonical ID Migration)
将所有表的 'symbol' 字段从旧格式（如 00700.HK, AAPL, ^HSI）转换为新格式（如 HK:STOCK:00700）。
影响表：Watchlist, Index, MarketDataDaily, MarketSnapshot, FinancialFundamentals, RawMarketData
"""
import sys
import os
import logging
from sqlmodel import Session, select, update

# 添加后端路径
sys.path.append('backend')
from database import engine
from models import Watchlist, Index, MarketDataDaily, MarketSnapshot, FinancialFundamentals, RawMarketData
from symbol_utils import get_canonical_id

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Migration")

def migrate_table(session, model_class, table_name):
    logger.info(f"正在迁移表: {table_name}...")
    
    # 获取该表所有不重复的 symbol
    records = session.exec(select(model_class)).all()
    count = 0
    
    # 建立映射以减少计算
    mapping = {}
    existing_keys_in_db = set() # 用于检测新标识是否已在该表中存在
    
    # 辅助函数：生成唯一键
    def get_unique_key(rec, sym, mkt):
        if hasattr(rec, 'timestamp'):
            return (sym, mkt, rec.timestamp)
        return (sym, mkt)

    # 先扫描已经符合规范的记录（防止后续冲突）
    for record in records:
        if ":" in record.symbol:
            existing_keys_in_db.add(get_unique_key(record, record.symbol, getattr(record, 'market', None)))

    for record in records:
        # 跳过已经符合规范的
        if ":" in record.symbol:
            continue
            
        old_symbol = record.symbol
        old_market = getattr(record, 'market', None)
        
        if old_symbol not in mapping:
            mapping[old_symbol] = get_canonical_id(old_symbol, old_market)
        
        new_symbol, target_market = mapping[old_symbol]
        unique_key = get_unique_key(record, new_symbol, target_market)
        
        # 处理重复性冲突
        if unique_key in existing_keys_in_db:
            logger.warning(f"  🗑️ 删除/跳过冲突项: {old_symbol} -> {new_symbol} (Key: {unique_key})")
            session.delete(record)
            continue
            
        existing_keys_in_db.add(unique_key)

        if old_symbol != new_symbol or old_market != target_market:
            record.symbol = new_symbol
            if hasattr(record, 'market'):
                record.market = target_market
            session.add(record)
            count += 1
            if count % 1000 == 0:
                session.commit()
                logger.info(f"  已处理 {count} 条记录...")
                
    session.commit()
    logger.info(f"✅ 表 {table_name} 迁移完成，更新了 {count} 条记录。")

def main():
    with Session(engine) as session:
        # 1. 基础配置表
        migrate_table(session, Watchlist, "Watchlist")
        migrate_table(session, Index, "Index")
        
        # 2. 核心数据表 (大数据量)
        migrate_table(session, MarketSnapshot, "MarketSnapshot")
        migrate_table(session, FinancialFundamentals, "FinancialFundamentals")
        migrate_table(session, MarketDataDaily, "MarketDataDaily")
        
        # 3. 原始数据表 (可选)
        migrate_table(session, RawMarketData, "RawMarketData")

    logger.info("🏁 所有数据表 ID 统一化迁移成功！")

if __name__ == "__main__":
    main()
