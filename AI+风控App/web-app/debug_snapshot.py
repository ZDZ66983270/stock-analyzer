
import sys
import os
# Adjust path to include backend
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.data_fetcher import DataFetcher
import logging

# Silence SQL logs
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.basicConfig(level=logging.ERROR) 


def debug_snapshot():
    fetcher = DataFetcher()
    
    # Check what fetch_latest_data returns for a stock
    print("Fetching snapshot for 600030.SH...")
    data = fetcher.fetch_latest_data('600030.SH', 'CN', force_refresh=True, save_db=False)
    print(f"Snapshot Data: {data}")
    
    if data:
        print(f"Date Field: {data.get('date')}")

    # Check HK
    print("\nFetching snapshot for 09988.HK...")
    data_hk = fetcher.fetch_latest_data('09988.HK', 'HK', force_refresh=True, save_db=False)
    print(f"Snapshot Data: {data_hk}")
    if data_hk:
        print(f"Date Field: {data_hk.get('date')}")

if __name__ == "__main__":
    debug_snapshot()
