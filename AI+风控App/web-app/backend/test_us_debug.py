from data_fetcher import DataFetcher
import logging

logging.basicConfig(level=logging.INFO)
fetcher = DataFetcher()

# Test 
symbol = "MSFT.OQ"
market = "US"

print(f"Fetching Yahoo Indicators for {symbol}...")
inds = fetcher.fetch_yahoo_indicators(symbol)
print("Yahoo Raw:", inds)

