import akshare as ak
import pandas as pd

def test_indices_compatibility():
    print("--- Testing Index Availability ---")
    
    # 1. CN Index: 000001.SS (ShangZheng)
    # Does stock_zh_a_spot_em include indices? Usually NO.
    # It includes stocks. 000001 is Ping An.
    # We might need ak.stock_zh_index_spot() for CN indices.
    print("\n[CN] Testing 000001 (Ping An) vs Index mechanisms...")
    try:
        df_cn = ak.stock_zh_a_spot_em()
        ping_an = df_cn[df_cn['代码'] == '000001']
        if not ping_an.empty:
            print(f"Standard Spot 000001 is: {ping_an.iloc[0]['名称']} (Ping An Bank)")
        
        # Now check Index Interface
        df_index = ak.stock_zh_index_spot()
        sh_index = df_index[df_index['名称'] == '上证指数']
        if not sh_index.empty:
            print(f"Found Index 000001 in Index-Spot: {sh_index.iloc[0]['代码']} - {sh_index.iloc[0]['名称']}")
    except Exception as e: print(e)

    # 2. HK Indices: 800000, 800700
    print("\n[HK] Testing 800000/800700...")
    try:
        # Check stock_hk_spot_em (Stocks)
        df_hk = ak.stock_hk_spot_em()
        match = df_hk[df_hk['代码'].isin(['800000', '800700'])]
        if not match.empty:
            print(f"Found in HK Stocks:\n{match[['代码', '名称']]}")
        else:
            print("Not found in HK Stock Spot. Checking Indices...")
            # Try index interface?
            pass
    except Exception as e: print(e)

    # 3. US Indices: SPY, NDX, DJI
    print("\n[US] Testing SPY, NDX, DJI in Sina...")
    try:
        df_us = ak.stock_us_spot() # Sina
        # SPY is an ETF, usually treated as stock.
        # NDX, DJI are indices.
        targets = ['SPY', 'NDX', 'DJI', '.DJI', '.IXIC', '.INX']
        match = df_us[df_us['symbol'].isin(targets)]
        if not match.empty:
            print(f"Found in US Spot (Sina):\n{match[['symbol', 'name', 'price']]}")
        else:
            print("No indices found in Sina Stock Spot.")
            
    except Exception as e: print(e)

if __name__ == "__main__":
    test_indices_compatibility()
