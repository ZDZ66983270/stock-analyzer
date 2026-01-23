#!/usr/bin/env python3
"""
强制从yfinance获取HK指数最新数据
"""
import sys
sys.path.append('backend')

from data_fetcher import DataFetcher
import yfinance as yf
from datetime import datetime

# 强制获取HSI今天的数据
symbols = [('HSI', '^HSI'), ('HSTECH', '^HSTECH')]

for symbol, yf_symbol in symbols:
    print(f"\n{'='*60}")
    print(f"强制从yfinance获取 {symbol}")
    print(f"{'='*60}")
    
    ticker = yf.Ticker(yf_symbol)
    hist = ticker.history(period='5d')  # 最近5天
    
    if not hist.empty:
        latest = hist.iloc[-1]
        latest_date = hist.index[-1]
        
        print(f"最新数据: {latest_date.strftime('%Y-%m-%d')}")
        print(f"收盘价: {latest['Close']:.2f}")
        print(f"涨跌幅: {((latest['Close'] - latest['Close'].shift(1)) / latest['Close'].shift(1) * 100):.2f}% (估算)")
        
        # 保存到数据库
        fetcher = DataFetcher()
        data = {
            'symbol': symbol,
            'market': 'HK',
            'price': float(latest['Close']),
            'close': float(latest['Close']),
            'open': float(latest['Open']),
            'high': float(latest['High']),
            'low': float(latest['Low']),
            'volume': int(latest['Volume']),
            'date': latest_date.strftime('%Y-%m-%d 16:00:00')
        }
        
        fetcher.save_snapshot(symbol, 'HK', data, 'yfinance')
        print(f"✅ 已保存到数据库")
    else:
        print(f"❌ yfinance也没有数据")
