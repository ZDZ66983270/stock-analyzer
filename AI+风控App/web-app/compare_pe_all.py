import sys
import yfinance as yf
from sqlmodel import Session, select
import time

# Ensure backend path is in sys.path
sys.path.append('backend')
from database import engine
from models import MarketDataDaily, Watchlist

def get_yfinance_symbol(market: str, code: str) -> str:
    """Simple converter for Watchlist symbol to Yahoo symbol"""
    if market == 'US':
        return code
    elif market == 'HK':
        # HK:STOCK:00700 -> 0700.HK
        # Remove leading zeros? Yahoo usually uses 4 digits with .HK
        # But 00700 -> 0700.HK, 09988 -> 9988.HK
        # 00005 -> 0005.HK
        clean_code = str(int(code)).zfill(4)
        return f"{clean_code}.HK"
    elif market == 'CN':
        # CN:STOCK:600030 -> 600030.SS
        # 6xxxx -> .SS
        # 0xxxx, 3xxxx -> .SZ
        if code.startswith('6'):
            return f"{code}.SS"
        else:
            return f"{code}.SZ"
    return code

def main():
    print(f"{'Code':<10} | {'Name':<10} | {'Yahoo PE':<10} | {'VERA PE':<10} | {'Diff (%)':<8} | {'Status':<10}")
    print("-" * 80)

    with Session(engine) as session:
        # Get all stocks from Watchlist (Filter by symbol pattern)
        stocks = session.exec(select(Watchlist).where(Watchlist.symbol.like('%:STOCK:%'))).all()
        
        # Sort by Market then Symbol
        stocks_sorted = sorted(stocks, key=lambda x: (x.market, x.symbol))

        valid_count = 0
        match_count = 0
        
        for stock in stocks_sorted:
            symbol_parts = stock.symbol.split(':')
            market = symbol_parts[0]
            code = symbol_parts[-1]
            
            # 1. Get VERA PE
            vera_pe = None
            daily = session.exec(
                select(MarketDataDaily)
                .where(MarketDataDaily.symbol == stock.symbol)
                .order_by(MarketDataDaily.timestamp.desc())
                .limit(1)
            ).first()
            
            if daily and daily.pe:
                vera_pe = daily.pe
            
            # 2. Get Yahoo PE
            yf_sym = get_yfinance_symbol(market, code)
            yahoo_pe = None
            
            try:
                ticker = yf.Ticker(yf_sym)
                # Fast info access
                info = ticker.fast_info
                # TPE is not in fast_info, need full info which is slow
                # Trying regular info but might be slow for batch
                # To speed up, we can fetch only once.
                # However, yfinance Ticker.info fetches everything.
                # Let's hope it's fast enough for ~20 stocks.
                full_info = ticker.info
                yahoo_pe = full_info.get('trailingPE')
            except Exception:
                pass
            
            # 3. Compare
            diff_str = "-"
            status = ""
            
            if vera_pe is not None and yahoo_pe is not None:
                if yahoo_pe == 0:
                     diff = 0
                else:
                    diff = abs(vera_pe - yahoo_pe) / yahoo_pe * 100
                diff_str = f"{diff:.1f}%"
                
                if diff < 10:
                    status = "✅ MATCH"
                    match_count += 1
                elif diff < 20: 
                    status = "⚠️ OK"
                    match_count += 1
                else:
                    status = "❌ DIFF"
                
                valid_count += 1
            elif vera_pe is None and yahoo_pe is None:
                 status = "⚪ NO DATA"
            elif vera_pe is None:
                 status = "❌ VERA NULL"
            elif yahoo_pe is None:
                 status = "⚠️ YF NULL"

            # Format outputs
            v_pe_str = f"{vera_pe:.2f}" if vera_pe else "None"
            y_pe_str = f"{yahoo_pe:.2f}" if yahoo_pe else "None"
            name_short = stock.name[:10]
            
            print(f"{code:<10} | {name_short:<10} | {y_pe_str:<10} | {v_pe_str:<10} | {diff_str:<8} | {status:<10}")
            
    print("-" * 80)
    if valid_count > 0:
        print(f"Total Valid Comparisons: {valid_count}")
        print(f"Match Rate (<20% Diff): {match_count}/{valid_count} ({match_count/valid_count*100:.1f}%)")
    else:
        print("No valid comparisons made.")

if __name__ == "__main__":
    main()
