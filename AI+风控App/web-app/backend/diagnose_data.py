import asyncio
from data_fetcher import DataFetcher
import json
import pandas as pd

# Helper to serialize pandas items
class SafeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, pd.Timestamp):
            return str(obj)
        return super().default(obj)

async def test():
    f = DataFetcher()
    symbols = [
        ("AAPL", "US"),
        ("00988.hk", "HK"), 
        ("601998.sh", "CN")
    ]
    
    print("--- DIAGNOSIS START ---")
    for sym, mkt in symbols:
        print(f"\nTesting {sym} [{mkt}]...")
        try:
            # Test fetch_latest_data which is used for real-time display
            data = await asyncio.to_thread(f.fetch_latest_data, sym, mkt)
            print(f"Result for {sym}:")
            print(json.dumps(data, indent=2, cls=SafeEncoder))
        except Exception as e:
            print(f"ERROR fetching {sym}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
