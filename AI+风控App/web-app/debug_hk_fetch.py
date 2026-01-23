
import sys
import logging
# Ensure backend import works
sys.path.append('.')
from daily_incremental_update import fetch_and_save_unified, get_yfinance_symbol

# Config logs to stderr
logging.basicConfig(level=logging.INFO)

symbol = "09988.HK"
market = "HK"
print(f"Testing Symbol: {symbol}")
converted = get_yfinance_symbol(symbol, market)
print(f"Converted Symbol: {converted}")

print("Running fetch...")
success = fetch_and_save_unified(symbol, market)
print(f"Success: {success}")
