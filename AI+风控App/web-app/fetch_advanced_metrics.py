
import sys
sys.path.append('backend')
from database import engine
from sqlmodel import Session, select
from models import MarketDataDaily, Watchlist, Index
import yfinance as yf
import akshare as ak
import pandas as pd
from datetime import datetime
import time

def get_cn_bulk_metrics():
    """Fetch current PE/PB/Cap for all CN stocks in one go."""
    print("🇨🇳 Fetching AkShare A-share spot data in bulk...")
    try:
        df = ak.stock_zh_a_spot_em()
        # Columns: 代码 (Code), 名称, 市盈率-动态, 市净率, 总市值, 成交额 (Turnover Amount)
        return df[['代码', '名称', '市盈率-动态', '市净率', '总市值', '成交额']]
    except Exception as e:
        print(f"   ❌ Failed to fetch CN bulk data: {e}")
        return None

def update_cn_metrics_bulk(session, symbols, df_bulk):
    if df_bulk is None or df_bulk.empty:
        return
    
    for symbol in symbols:
        code = symbol.split(".")[0]
        match = df_bulk[df_bulk['代码'] == code]
        if match.empty:
            print(f"   ⚠️ No match in bulk data for {symbol}")
            continue
            
        row = match.iloc[0]
        # Get latest record
        record = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.symbol == symbol)
            .order_by(MarketDataDaily.timestamp.desc())
            .limit(1)
        ).first()
        
        if record:
            try:
                pe = row.get('市盈率-动态')
                record.pe = float(pe) if pd.notnull(pe) and pe != '-' else None
                pb = row.get('市净率')
                record.pb = float(pb) if pd.notnull(pb) and pb != '-' else None
                mcap = row.get('总市值')
                record.market_cap = float(mcap) if pd.notnull(mcap) and mcap != '-' else None
                # record.turnover (Note: current spot turnover might be different from daily historical turnover)
                
                session.add(record)
                print(f"   ✅ Updated {symbol}: PE={record.pe}, PB={record.pb}")
            except Exception as e:
                print(f"   ❌ Error updating {symbol}: {e}")
    session.commit()

def update_us_hk_metrics(session, symbol, market):
    print(f"🌎 Fetching Yahoo info for {symbol} ({market})...")
    try:
        yf_sym = symbol
        # Handle index mappings if needed, but Tickers usually match for ^SPX etc.
        # though info() might be empty for indices.
        
        ticker = yf.Ticker(yf_sym)
        info = ticker.info
        
        # Get latest record
        record = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.symbol == symbol)
            .order_by(MarketDataDaily.timestamp.desc())
            .limit(1)
        ).first()
        
        if record:
            record.pe = info.get('trailingPE') or info.get('forwardPE')
            record.pb = info.get('priceToBook')
            record.ps = info.get('priceToSalesTrailing12Months')
            # Use raw dividendYield if it's already percentage (0.75 for 0.75%)
            record.dividend_yield = info.get('dividendYield')
            record.market_cap = info.get('marketCap')
            record.eps = info.get('trailingEps')
            
            session.add(record)
            session.commit()
            print(f"   ✅ Updated {symbol}: PE={record.pe}, DY={record.dividend_yield}")
        else:
            print(f"   ⚠️ No daily data for {symbol}")
            
    except Exception as e:
        print(f"   ❌ Failed to fetch {symbol}: {e}")

def main():
    with Session(engine) as session:
        watchlist = session.exec(select(Watchlist)).all()
        indices = session.exec(select(Index)).all()
        
        cn_symbols = []
        other_tasks = []
        
        for item in list(watchlist) + list(indices):
            market = getattr(item, 'market', 'US')
            # 从 Canonical ID 提取纯代码
            code = item.symbol.split(':')[-1] if ':' in item.symbol else item.symbol
            if market == 'CN' and not code.startswith('^'):
                cn_symbols.append(code)
            else:
                other_tasks.append((code, market))
        
        # 1. Update CN in bulk
        if cn_symbols:
            df_cn = get_cn_bulk_metrics()
            update_cn_metrics_bulk(session, cn_symbols, df_cn)
        
        # 2. Update Others individually
        for symbol, market in other_tasks:
            update_us_hk_metrics(session, symbol, market)
            time.sleep(0.5)

if __name__ == "__main__":
    main()
