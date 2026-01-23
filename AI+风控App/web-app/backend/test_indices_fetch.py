import akshare as ak
import pandas as pd

def test_indices():
    print("--- Searching for Indices ---")
    
    # 1. CN Index (ShangZheng 000001)
    print("\n1. CN Index (Spot A)...")
    try:
        # stock_zh_index_spot?
        df = ak.stock_zh_index_spot()
        # Look for 上证指数
        match = df[df['名称'].str.contains("上证指数")]
        print(match[['代码', '名称', '最新价', '涨跌幅']])
    except Exception as e:
        print(f"CN Index Failed: {e}")

    # 2. HK Indices (HSI, Tech)
    print("\n2. HK Indices...")
    try:
        # stock_hk_index_spot_em? Or stock_hk_index_spot_sina?
        # Let's try em first
        df = ak.stock_hk_index_spot_em() # Does this exist? Or stock_hk_index_spot?
        # Check names
        targets = ["恒生指数", "恒生科技"]
        for t in targets:
            match = df[df['名称'].str.contains(t)]
            if not match.empty:
                print(match[['代码', '名称', '最新价', '涨跌幅']])
    except AttributeError:
        print("stock_hk_index_spot_em not found. Trying stock_hk_index_spot_sina...")
        try:
           df = ak.stock_hk_index_spot_sina()
           print(df.head())
        except Exception as e: print(e)
    except Exception as e:
        print(f"HK Index Failed: {e}")

    # 3. US Indices (Dow, Nasdaq, SP500)
    print("\n3. US Indices...")
    try:
        # stock_us_index_spot_em?
        # Or maybe they are in stock_us_spot_em with special codes?
        # Often .DJI, .IXIC
        df = ak.index_us_stock_sina() # Sina has US indices?
        # Or em?
        # Let's try to search in stock_us_spot_em (which we downloaded to csv!)
        pass
    except Exception as e:
        print(f"US Index API Check Failed: {e}")

if __name__ == "__main__":
    test_indices()
