import sys
from sqlmodel import Session, select
import logging

# Setup paths
sys.path.append('backend')
from database import engine
from models import MarketDataDaily, Watchlist, FinancialFundamentals
from valuation_calculator import (
    get_ttm_net_income, 
    compute_ttm_eps_per_unit,
    get_shares_outstanding
)
from symbols_config import SYMBOLS_CONFIG, normalize_code

# Configure logging to suppress SQL info
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

def diagnose():
    print(f"{'代码':10s} | {'Mkt/Fin':7s} | {'TTM净利(亿)':12s} | {'股本(亿)':10s} | {'基础EPS':8s} | {'汇率':5s} | {'最终EPS':8s} | {'收盘价':8s} | {'计算PE':8s}")
    print('-'*115)

    with Session(engine) as session:
        # Load stocks
        stocks = session.exec(select(Watchlist).where(Watchlist.symbol.like('%:STOCK:%'))).all()
        
        # Preload financials
        all_fins = session.exec(
            select(FinancialFundamentals)
            .order_by(FinancialFundamentals.symbol, FinancialFundamentals.as_of_date.desc())
        ).all()
        fin_cache = {}
        for f in all_fins:
            if f.symbol not in fin_cache: fin_cache[f.symbol] = []
            fin_cache[f.symbol].append(f)

        for stock in sorted(stocks, key=lambda x: (x.market, x.symbol)):
            symbol = stock.symbol
            market = stock.market
            market_currency = {'US': 'USD', 'HK': 'HKD', 'CN': 'CNY'}.get(market, 'USD')
            
            # 1. TTM Income
            fins = fin_cache.get(symbol, [])
            if not fins: continue
            
            latest_date = '2026-01-08' 
            ttm_income, fin_currency = get_ttm_net_income(fins, latest_date)
            
            # 2. Shares
            # Note: get_shares_outstanding prints warnings if it fails, which is fine
            shares = get_shares_outstanding(symbol, market)
            
            # 3. Raw EPS
            raw_eps = 0.0
            if ttm_income and shares:
                raw_eps = ttm_income / shares
            
            # 4. Exchange & Final EPS
            simple_code = normalize_code(symbol)
            config = SYMBOLS_CONFIG.get(simple_code, {})
            adr_ratio = config.get('adr_ratio', 1.0)
            
            final_eps = compute_ttm_eps_per_unit(
                ttm_income,
                shares,
                fin_currency or market_currency,
                market_currency,
                adr_ratio
            )
            
            # Derive effective exchange rate used
            exchange_rate_used = 1.0
            if raw_eps and final_eps:
                exchange_rate_used = final_eps / raw_eps / adr_ratio

            # 5. PE
            latest_daily = session.exec(
                 select(MarketDataDaily)
                 .where(MarketDataDaily.symbol == symbol)
                 .order_by(MarketDataDaily.timestamp.desc())
                 .limit(1)
            ).first()
            close = latest_daily.close if latest_daily else 0
            pe = close / final_eps if final_eps and close and final_eps != 0 else 0
            
            code = symbol.split(':')[-1]
            mkt_fin_curr = f"{market_currency}/{fin_currency}"
            
            income_disp = ttm_income / 1e8 if ttm_income else 0
            shares_disp = shares / 1e8 if shares else 0
            
            print(f"{code:10s} | {mkt_fin_curr:7s} | {income_disp:12.2f} | {shares_disp:10.2f} | {raw_eps:8.4f} | {exchange_rate_used:5.2f} | {final_eps:8.4f} | {close:8.2f} | {pe:8.2f}")

if __name__ == "__main__":
    diagnose()
