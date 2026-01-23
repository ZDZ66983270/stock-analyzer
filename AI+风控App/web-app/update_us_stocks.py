
import sys
import time
sys.path.insert(0, 'backend')

from daily_incremental_update import fetch_and_save_unified
from advanced_metrics import update_all_metrics

# US symbols that need updating
US_SYMBOLS = [
    "^DJI",   # Dow Jones
    "^NDX",   # Nasdaq 100
    "^SPX",   # S&P 500
    "MSFT",   # Microsoft
    "TSLA"    # Tesla
]

print("🔄 Updating US Stocks and Indices...")

for symbol in US_SYMBOLS:
    print(f"   Fetching {symbol}...", end=" ")
    if fetch_and_save_unified(symbol, "US"):
        print("✅")
    else:
        print("❌")
    time.sleep(1)

print("\n📊 Updating Advanced Metrics...")
try:
    update_all_metrics()
    print("✅ Metrics Updated")
except Exception as e:
    print(f"⚠️ Failed: {e}")

print("\n🎉 US Update Complete!")
