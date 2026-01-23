from data_fetcher import DataFetcher
import logging

logging.basicConfig(level=logging.INFO)
f = DataFetcher()
print("Fetching Yahoo Indicators for TSLA.OQ...")
res = f.fetch_yahoo_indicators("TSLA.OQ")
print(f"Result: {res}")
if res:
    print(f"Prev Close: {res.get('prev_close')}")
