from data_fetcher import DataFetcher
import logging

def main():
    logging.basicConfig(level=logging.INFO)
    f = DataFetcher()
    print("Refilling TSLA data (History + Snapshot)...")
    
    # 1. Fetch History (Min/Daily)
    f.fetch_single_stock("TSLA.OQ")
    
    # 2. Fetch Snapshot (for Price/Change/PctChange in Watchlist)
    # fetch_latest_data saves to DB by default
    print("Fetching Snapshot...")
    f.fetch_latest_data("TSLA.OQ", "US", force_refresh=True)
    
    print("Refill complete. Please verify Watchlist.")

if __name__ == "__main__":
    main()
