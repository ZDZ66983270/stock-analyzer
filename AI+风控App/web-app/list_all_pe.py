#!/usr/bin/env python3
"""
列出所有个股的 PE 和 TTM EPS 数据
"""
import sys
sys.path.append('backend')
from sqlmodel import Session, select
from backend.database import engine
from backend.models import MarketDataDaily, Watchlist

print("="*120)
print(f"所有个股 PE 和 TTM EPS 数据")
print("="*120)
print(f"{'股票代码':<20} {'名称':<20} {'市场':<8} {'VERA PE':<12} {'TTM EPS':<12} {'收盘价':<12} {'日期':<12}")
print("-"*120)

with Session(engine) as session:
    # 从 Watchlist 获取所有股票（排除指数）
    watchlist = session.exec(
        select(Watchlist)
        .order_by(Watchlist.market, Watchlist.symbol)
    ).all()
    
    # 过滤出股票（symbol 包含 STOCK）
    stocks = [w for w in watchlist if 'STOCK' in w.symbol]
    
    for item in stocks:
        symbol = item.symbol
        name = item.name or symbol.split(':')[-1]
        market = item.market
        
        # 获取最新日线数据
        daily = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.symbol == symbol)
            .order_by(MarketDataDaily.timestamp.desc())
            .limit(1)
        ).first()
        
        if daily:
            pe_str = f'{daily.pe:.2f}' if daily.pe else 'N/A'
            eps_str = f'{daily.eps:.2f}' if daily.eps else 'N/A'
            price_str = f'${daily.close:.2f}' if daily.close else 'N/A'
            
            # timestamp 可能是字符串或 datetime
            if daily.timestamp:
                if isinstance(daily.timestamp, str):
                    date_str = daily.timestamp[:10]  # 取前10个字符 YYYY-MM-DD
                else:
                    date_str = daily.timestamp.strftime('%Y-%m-%d')
            else:
                date_str = 'N/A'
        else:
            pe_str = 'N/A'
            eps_str = 'N/A'
            price_str = 'N/A'
            date_str = 'N/A'
        
        print(f'{symbol:<20} {name:<20} {market:<8} {pe_str:<12} {eps_str:<12} {price_str:<12} {date_str:<12}')

print("="*120)

# 统计
print(f"\n按市场统计:")
print("-"*120)

with Session(engine) as session:
    for market in ['US', 'HK', 'CN']:
        watchlist = session.exec(
            select(Watchlist)
            .where(Watchlist.market == market)
        ).all()
        
        # 过滤出股票
        stocks = [w for w in watchlist if 'STOCK' in w.symbol]
        total = len(stocks)
        has_pe = 0
        
        for item in stocks:
            daily = session.exec(
                select(MarketDataDaily)
                .where(MarketDataDaily.symbol == item.symbol)
                .order_by(MarketDataDaily.timestamp.desc())
                .limit(1)
            ).first()
            
            if daily and daily.pe:
                has_pe += 1
        
        market_name = {'US': '美股', 'HK': '港股', 'CN': 'A股'}.get(market, market)
        print(f"{market_name}: {has_pe}/{total} 个股票有 PE 数据 ({has_pe/total*100:.1f}%)" if total > 0 else f"{market_name}: 无数据")

print("="*120)
