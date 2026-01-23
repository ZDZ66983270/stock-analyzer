import pandas as pd
from sqlmodel import Session, select
from backend.db import engine
from backend.models import MarketDataDaily, Watchlist

# Definition from add_market_proxies.py
PROXIES = {
    # Anchors
    "SPY": "SPDR S&P 500 ETF Trust",
    "QQQ": "Invesco QQQ Trust",
    "DIA": "SPDR Dow Jones Industrial Average ETF Trust",
    
    # Sectors
    "XLK": "Technology Select Sector SPDR Fund",
    "XLF": "Financial Select Sector SPDR Fund",
    "XLV": "Health Care Select Sector SPDR Fund",
    "XLP": "Consumer Staples Select Sector SPDR Fund",
    "XLY": "Consumer Discretionary Select Sector SPDR Fund",
    "XLI": "Industrial Select Sector SPDR Fund",
    "XLE": "Energy Select Sector SPDR Fund",
    "XLB": "Materials Select Sector SPDR Fund",
    "XLU": "Utilities Select Sector SPDR Fund",
    "XLRE": "Real Estate Select Sector SPDR Fund",
    "XLC": "Communication Services Select Sector SPDR Fund",
    
    # Styles & Defensive
    "VUG": "Vanguard Growth ETF",
    "VTV": "Vanguard Value ETF",
    "VYM": "Vanguard High Dividend Yield ETF",
    "IWM": "iShares Russell 2000 ETF",
    "USMV": "iShares MSCI USA Min Vol Factor ETF",
    "TLT": "iShares 20+ Year Treasury Bond ETF",
    "GLD": "SPDR Gold Shares"
}

def export_proxies():
    print(f"🚀 Exporting Proxy Report for {len(PROXIES)} assets...")
    
    data = []
    
    with Session(engine) as session:
        for symbol, name in PROXIES.items():
            # Canonical ID construction (Approximation, safer to query Watchlist)
            # Assuming US:STOCK:SYMBOL or just checking suffix
            # But add_market_proxies inserts them as 'US' market.
            # Let's search by symbol in Watchlist first to get proper ID?
            # Actually, add_market_proxies.py inserts 'SPY', 'QQQ' etc into symbol column directly?
            # Let's check Watchlist to be sure about the 'symbol' format stored.
            
            # Try exact match first (if stored as pure ticker)
            w_item = session.exec(select(Watchlist).where(Watchlist.symbol == symbol)).first()
            if not w_item:
                 # Try canonical format US:STOCK:{symbol} or US:ETF:{symbol}
                 # Proxies are mostly ETFs
                 w_item = session.exec(select(Watchlist).where(Watchlist.symbol == f"US:ETF:{symbol}")).first()
                 
            real_symbol = w_item.symbol if w_item else symbol
            
            # Get latest Daily Data
            daily = session.exec(
                select(MarketDataDaily)
                .where(MarketDataDaily.symbol == real_symbol)
                .order_by(MarketDataDaily.timestamp.desc())
            ).first()
            
            row = {
                'symbol': real_symbol,
                'name': name,
                'date': daily.timestamp if daily else None,
                'close': daily.close if daily else None,
                'pe': daily.pe if daily else None,
                'pe_ttm': daily.pe_ttm if daily else None,
                'pb': daily.pb if daily else None,
                'source_data_present': "Yes" if daily else "No"
            }
            data.append(row)

    df = pd.DataFrame(data)
    output_path = "outputs/proxies_report.csv"
    df.to_csv(output_path, index=False)
    print(f"✅ Exported to {output_path}")
    print(df[['symbol', 'date', 'pe', 'pe_ttm']])

if __name__ == "__main__":
    export_proxies()
