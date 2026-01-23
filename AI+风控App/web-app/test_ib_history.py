import asyncio
from ib_insync import *
import pandas as pd

def test_ib_fetch():
    print("🚀 Connecting to IB (TWS/Gateway)...")
    ib = IB()
    
    # Common ports: 
    # 7497: TWS Paper Trading (Default)
    # 7496: TWS Live Trading
    # 4001: IB Gateway Live
    # 4002: IB Gateway Paper
    
    port = 4002
    try:
        ib.connect('127.0.0.1', port, clientId=1)
    except Exception as e:
        print(f"❌ Connection failed on port {port}: {e}")
        print("💡 Please ensure TWS or IB Gateway is running and API is enabled.")
        return

    print("✅ Connected!")

    # Define Contract
    contract = Stock('AAPL', 'SMART', 'USD')
    print(f"📋 Contract: {contract}")

    # Request Historical Data
    # durationStr: '1 Y', '1 M', '1 D', etc.
    # barSizeSetting: '1 day', '1 min', etc.
    print("📉 Requesting Historical Data (1 Month, Daily)...")
    
    bars = ib.reqHistoricalData(
        contract,
        endDateTime='',
        durationStr='1 M',
        barSizeSetting='1 day',
        whatToShow='TRADES',
        useRTH=True
    )

    if not bars:
        print("⚠️ No data received.")
    else:
        print(f"✅ Received {len(bars)} bars.")
        
        # Convert to DataFrame
        df = util.df(bars)
        
        print("\n" + "="*30)
        print("📊 Data Fields (Columns):")
        print("="*30)
        print(df.columns.tolist())
        
        print("\n" + "="*30)
        print("📋 Data Types:")
        print("="*30)
        print(df.dtypes)
        
        print("\n" + "="*30)
        print("📉 Data Sample:")
        print("="*30)
        print(df.head())
        print("...")
        print(df.tail())

    ib.disconnect()

if __name__ == "__main__":
    # ib_insync uses asyncio, but for simple scripts IB() handles the loop or we can run via run()
    # verify if we are in a jupyter env or script
    test_ib_fetch()
