import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlmodel import create_engine, Session, select
from backend.models import MarketSnapshot, MarketDataDaily

def main():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend', 'database.db'))
    engine = create_engine(f"sqlite:///{db_path}")
    
    print(f"查询数据库: {db_path}\n")
    
    with Session(engine) as session:
        # 获取所有快照数据
        snapshots = session.exec(select(MarketSnapshot)).all()
        snapshot_map = {(s.symbol, s.market): s for s in snapshots}
        
        # 获取所有symbol的最新daily数据
        # 需要按symbol分组获取最新的
        from sqlalchemy import func
        
        # 先获取所有唯一的symbol+market组合
        symbols_stmt = select(MarketDataDaily.symbol, MarketDataDaily.market).distinct()
        symbols = session.exec(symbols_stmt).all()
        
        daily_map = {}
        for symbol, market in symbols:
            stmt = select(MarketDataDaily).where(
                MarketDataDaily.symbol == symbol,
                MarketDataDaily.market == market
            ).order_by(MarketDataDaily.timestamp.desc()).limit(1)
            latest = session.exec(stmt).first()
            if latest:
                daily_map[(symbol, market)] = latest
        
        # 合并所有symbol
        all_keys = set(snapshot_map.keys()) | set(daily_map.keys())
        
        # 按市场分组
        markets = {'US': [], 'CN': [], 'HK': []}
        for key in all_keys:
            symbol, market = key
            if market in markets:
                markets[market].append(key)
        
        print(f"{'市场':<6} {'代码':<12} {'快照时间':<20} {'快照价格':<10} {'快照涨跌':<10} {'Daily时间':<20} {'Daily价格':<10} {'Daily涨跌':<10}")
        print("=" * 120)
        
        for market_name in ['US', 'CN', 'HK']:
            if markets[market_name]:
                print(f"\n=== {market_name} 市场 ===")
                for key in sorted(markets[market_name]):
                    symbol, market = key
                    
                    # Snapshot数据
                    snap = snapshot_map.get(key)
                    snap_time = snap.timestamp if snap else "N/A"
                    snap_price = f"{snap.price:.2f}" if snap else "N/A"
                    snap_pct = f"{snap.pct_change:+.2f}%" if snap and snap.pct_change is not None else "N/A"
                    
                    # Daily数据
                    daily = daily_map.get(key)
                    daily_time = daily.timestamp if daily else "N/A"
                    daily_price = f"{daily.close:.2f}" if daily else "N/A"
                    daily_pct = f"{daily.pct_change:+.2f}%" if daily and daily.pct_change is not None else "N/A"
                    
                    print(f"{market:<6} {symbol:<12} {str(snap_time):<20} {snap_price:<10} {snap_pct:<10} {str(daily_time):<20} {daily_price:<10} {daily_pct:<10}")

if __name__ == "__main__":
    main()
