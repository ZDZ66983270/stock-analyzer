#!/usr/bin/env python3
"""
用 symbols.txt 覆盖 Watchlist 表
"""
import sys
from sqlmodel import Session, select, delete
from backend.database import engine
from backend.models import Watchlist
from backend.symbol_utils import get_canonical_id
from datetime import datetime

def parse_symbols_txt(filepath='imports/symbols.txt'):
    """解析 symbols.txt 文件"""
    symbols = []
    current_section = None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # Section headers
            if line.startswith('#'):
                if 'A股' in line and 'ETF' not in line:
                    current_section = 'CN'
                elif '港股' in line and 'ETF' not in line:
                    current_section = 'HK'
                elif '美股' in line and 'ETF' not in line:
                    current_section = 'US'
                elif '加密货币' in line:
                    current_section = 'CRYPTO'
                elif 'ETF' in line:
                    current_section = 'ETF'
                elif '指数' in line:
                    current_section = 'INDEX'
                continue
            
            # Parse symbol
            if current_section and current_section not in ['ETF', 'INDEX']:
                symbols.append({
                    'raw_symbol': line,
                    'market': current_section
                })
    
    return symbols

def main():
    print("🚀 用 symbols.txt 覆盖 Watchlist...")
    
    # 1. Parse symbols.txt
    symbols = parse_symbols_txt()
    
    if not symbols:
        print("❌ symbols.txt 中没有找到有效的股票符号")
        return
    
    print(f"📋 从 symbols.txt 读取到 {len(symbols)} 个符号")
    
    with Session(engine) as session:
        # 2. Clear existing Watchlist
        print("🗑️  清空现有 Watchlist...")
        session.exec(delete(Watchlist))
        session.commit()
        
        # 3. Add symbols from symbols.txt
        print("➕ 添加 symbols.txt 中的符号...")
        added_count = 0
        
        for item in symbols:
            raw_symbol = item['raw_symbol']
            market = item['market']
            
            # Get canonical ID
            canonical_id, detected_market = get_canonical_id(raw_symbol, market)
            
            # Use detected market if available
            final_market = detected_market or market
            
            # Create Watchlist entry
            watchlist_item = Watchlist(
                symbol=canonical_id,
                name=raw_symbol,  # Will be updated later by data fetch
                market=final_market,
                added_at=datetime.now()  # Use datetime object
            )
            
            session.add(watchlist_item)
            added_count += 1
            print(f"  ✅ {canonical_id} ({final_market})")
        
        session.commit()
        
        print(f"\n✅ Watchlist 已更新: {added_count} 个资产")
        
        # 4. Verify
        final_count = session.exec(select(Watchlist)).all()
        print(f"📊 当前 Watchlist 总数: {len(final_count)}")

if __name__ == "__main__":
    main()
