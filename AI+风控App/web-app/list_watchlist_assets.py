"""列出 Watchlist 表中所有资产的 Canonical ID"""
from backend.database import engine
from sqlalchemy import text
from sqlmodel import Session

def main():
    with Session(engine) as session:
        # 查询所有资产
        result = session.exec(text("""
            SELECT symbol, name, market 
            FROM watchlist 
            ORDER BY market, symbol
        """)).all()
        
        print("=" * 80)
        print(f"Watchlist 表中的所有资产 (共 {len(result)} 个)")
        print("=" * 80)
        
        # 按市场分组显示
        current_market = None
        for row in result:
            symbol, name, market = row
            
            # 打印市场分隔符
            if market != current_market:
                current_market = market
                print(f"\n【{market} 市场】")
                print("-" * 80)
            
            # 打印资产信息
            asset_type = symbol.split(':')[1] if ':' in symbol else 'UNKNOWN'
            print(f"  {symbol:30} {name:25} [{asset_type}]")
        
        # 统计信息
        print("\n" + "=" * 80)
        print("统计信息:")
        print("=" * 80)
        
        stats = session.exec(text("""
            SELECT market, COUNT(*) as count
            FROM watchlist
            GROUP BY market
            ORDER BY market
        """)).all()
        
        for market, count in stats:
            print(f"  {market:5} 市场: {count:3} 个资产")
        
        print(f"\n  总计: {len(result)} 个资产")

if __name__ == "__main__":
    main()
