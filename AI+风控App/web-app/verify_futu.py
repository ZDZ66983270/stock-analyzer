
import sys
import os
import logging

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Mock logging
logging.basicConfig(level=logging.INFO)

from advanced_metrics import fetch_hk_pe_futu

def verify():
    symbol = "HK:STOCK:00700"
    print(f"Testing Futu Fetch for {symbol}...")
    result = fetch_hk_pe_futu(symbol)
    
    if result:
        pe_ttm, pe_static, mcap = result
        print(f"✅ Success! Data from Futu:")
        print(f"   PE TTM:    {pe_ttm}")
        print(f"   PE Static: {pe_static}")
        print(f"   MarketCap: {mcap}")
        
        # Also verification of yfinance fallback logic check not needed if Futu works
    else:
        print("❌ Failed or returned None. Make sure Futu OpenD is running on port 11111.")

if __name__ == "__main__":
    verify()
