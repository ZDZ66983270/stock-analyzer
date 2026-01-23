import akshare as ak
import pandas as pd

print("Testing Sina HK Spot Interface (stock_hk_spot)...")
try:
    df = ak.stock_hk_spot()
    print(f"Success! Fetched {len(df)} rows.")
    print("Columns:", df.columns.tolist())
    
    # Check for Alibaba (09988)
    # Sina usually uses 5 digits? or symbol column format?
    # Output cols: symbol, name, engname...
    
    alibaba = df[df['symbol'].astype(str).str.contains('09988')]
    if not alibaba.empty:
        print("\nFound Alibaba:")
        print(alibaba.iloc[0])
        
    # Save to CSV for User Inspection
    import os
    save_path = os.path.join(os.path.dirname(__file__), "market_data_library", "snapshot_hk.csv")
    df.to_csv(save_path, index=False)
    print(f"\nSaved full snapshot to {save_path}")

except Exception as e:
    print(f"Error: {e}")
