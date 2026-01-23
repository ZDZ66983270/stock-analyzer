
import sys
import os
# Ensure backend can be imported
base_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(base_dir, 'backend')
if base_dir not in sys.path: sys.path.append(base_dir)
if backend_dir not in sys.path: sys.path.append(backend_dir)

from backend.valuation_calculator import get_shares_outstanding
from backend.symbol_utils import get_yahoo_symbol
import yfinance as yf

def test_shares(symbol, market):
    print(f"--- Testing {symbol} ({market}) ---")
    shares = get_shares_outstanding(symbol, market)
    print(f"Result Shares: {shares}")
    
    # Debug raw
    yf_sym = get_yahoo_symbol(symbol.split(':')[-1], market)
    print(f"Yahoo Symbol: {yf_sym}")
    try:
        t = yf.Ticker(yf_sym)
        i = t.info
        print(f"Raw sharesOutstanding: {i.get('sharesOutstanding')}")
        print(f"Raw impliedSharesOutstanding: {i.get('impliedSharesOutstanding')}")
        print(f"Raw marketCap: {i.get('marketCap')}")
        print(f"Raw price: {i.get('currentPrice') or i.get('regularMarketPreviousClose')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_shares("US:STOCK:META", "US")
    test_shares("HK:STOCK:00005", "HK")
