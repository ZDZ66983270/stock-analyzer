"""
测试新的Index表架构
验证数据获取是否同时包含Watchlist和Index
"""
import sys
sys.path.insert(0, 'backend')

from database import engine
from sqlmodel import Session
from symbol_utils import get_all_symbols_to_update, get_symbols_by_market

print("="*60)
print("测试Index表架构")
print("="*60)

with Session(engine) as session:
    # 1. 获取所有符号
    print("\n1. 获取所有需要更新的符号...")
    all_symbols = get_all_symbols_to_update(session)
    
    print(f"   总计: {len(all_symbols)} 个")
    
    # 按来源分组统计
    watchlist_count = sum(1 for s in all_symbols if s['source'] == 'watchlist')
    index_count = sum(1 for s in all_symbols if s['source'] == 'index')
    
    print(f"   - Watchlist: {watchlist_count} 个")
    print(f"   - Index: {index_count} 个")
    
    # 2. 按市场分组
    print("\n2. 按市场分组...")
    for market in ['US', 'HK', 'CN']:
        market_symbols = get_symbols_by_market(session, market)
        print(f"\n   {market} 市场: {len(market_symbols)} 个")
        for item in market_symbols:
            source_icon = "📊" if item['source'] == 'index' else "📈"
            print(f"      {source_icon} {item['symbol']}: {item['name']}")

print("\n" + "="*60)
print("✅ 测试完成")
print("="*60)
