#!/usr/bin/env python3
"""
列出所有个股的 PE 对比数据
格式：资产名称、收盘日期、收盘价、VERA PE、Yahoo PE
"""
import sys
sys.path.append('backend')
from sqlmodel import Session, select
from backend.database import engine
from backend.models import MarketDataDaily, Watchlist
from backend.symbols_config import get_yfinance_symbol
import yfinance as yf

print("="*120)
print(f"{'资产名称':<25} {'收盘日期':<12} {'收盘价':<12} {'VERA PE':<12} {'Yahoo PE':<12} {'偏差':<10}")
print("="*120)

with Session(engine) as session:
    # 从 Watchlist 获取所有股票
    watchlist = session.exec(
        select(Watchlist)
        .order_by(Watchlist.market, Watchlist.symbol)
    ).all()
    
    # 过滤出股票
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
        
        if not daily:
            continue
        
        # VERA 数据
        vera_pe = f'{daily.pe:.2f}' if daily.pe else 'N/A'
        price = f'${daily.close:.2f}' if daily.close else 'N/A'
        
        # 日期处理
        if daily.timestamp:
            if isinstance(daily.timestamp, str):
                date_str = daily.timestamp[:10]
            else:
                date_str = daily.timestamp.strftime('%Y-%m-%d')
        else:
            date_str = 'N/A'
        
        # 获取 Yahoo PE
        try:
            yf_symbol = get_yfinance_symbol(symbol, market)
            ticker = yf.Ticker(yf_symbol)
            yahoo_pe = ticker.info.get('trailingPE')
            
            if yahoo_pe:
                yahoo_pe_str = f'{yahoo_pe:.2f}'
                
                # 计算偏差
                if daily.pe and yahoo_pe:
                    diff_pct = abs(daily.pe - yahoo_pe) / yahoo_pe * 100
                    diff_str = f'{diff_pct:.1f}%'
                else:
                    diff_str = 'N/A'
            else:
                yahoo_pe_str = 'N/A'
                diff_str = 'N/A'
        except:
            yahoo_pe_str = 'Error'
            diff_str = 'N/A'
        
        print(f'{name:<25} {date_str:<12} {price:<12} {vera_pe:<12} {yahoo_pe_str:<12} {diff_str:<10}')

print("="*120)
