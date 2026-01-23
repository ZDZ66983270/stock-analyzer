from sqlmodel import Session
from backend.database import engine
from fetch_financials import fetch_yahoo_financials, upsert_financials

def main():
    symbol = "US:STOCK:TSLA"
    print(f"🚀 Fetching Quarterly Data for {symbol}...")
    
    # This now fetches both Annual and Quarterly due to my previous code change
    data_list = fetch_yahoo_financials(symbol)
    
    if data_list:
        print(f"✅ Fetched {len(data_list)} records.")
        with Session(engine) as session:
            for d in data_list:
                upsert_financials(session, d)
            session.commit()
    else:
        print("❌ No data found.")

if __name__ == "__main__":
    main()
