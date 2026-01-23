import asyncio
from tasks import fetch_market_data
from market_schedule import MarketSchedule

async def trigger():
    print("--- Manual Task Trigger ---")
    # Force check US market
    market = "US"
    print(f"Checking {market}...")
    is_open, reason = MarketSchedule.is_market_open(market)
    print(f"Market Open: {is_open} ({reason})")
    
    await fetch_market_data(market) # This runs the logic we debugged
    print("--- Task Completed ---")

if __name__ == "__main__":
    asyncio.run(trigger())
