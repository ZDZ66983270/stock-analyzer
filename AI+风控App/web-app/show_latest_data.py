#!/usr/bin/env python3
"""
查看所有资产的最新收盘价、PE和时间戳
"""
import sys
sys.path.append('backend')

from sqlmodel import Session, select
from backend.database import engine
from backend.models import MarketDataDaily, Watchlist, Index
import logging

# 禁用SQL日志
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

with Session(engine) as session:
    # 获取所有资产
    watchlist = session.exec(select(Watchlist)).all()
    indices = session.exec(select(Index)).all()
    
    all_assets = [(w.symbol, w.name, w.market, 'Stock/ETF') for w in watchlist]
    all_assets += [(i.symbol, i.name, i.market, 'Index') for i in indices]
    
    print('='*130)
    print(f'{'Symbol':<25} | {'Name':<12} | {'Market':<6} | {'Type':<10} | {'Close':<10} | {'PE':<10} | {'PB':<10} | {'Timestamp':<20}')
    print('='*130)
    
    for symbol, name, market, asset_type in sorted(all_assets, key=lambda x: (x[2], x[0])):
        # 获取最新的日线数据
        latest = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.symbol == symbol)
            .order_by(MarketDataDaily.timestamp.desc())
            .limit(1)
        ).first()
        
        if latest:
            close = f'{latest.close:.2f}' if latest.close else 'N/A'
            pe = f'{latest.pe:.2f}' if latest.pe else 'N/A'
            pb = f'{latest.pb:.2f}' if latest.pb else 'N/A'
            timestamp = latest.timestamp
            print(f'{symbol:<25} | {name:<12} | {market:<6} | {asset_type:<10} | {close:<10} | {pe:<10} | {pb:<10} | {timestamp:<20}')
        else:
            print(f'{symbol:<25} | {name:<12} | {market:<6} | {asset_type:<10} | {'NO DATA':<10} | {'N/A':<10} | {'N/A':<10} | {'N/A':<20}')
    
    print('='*130)
