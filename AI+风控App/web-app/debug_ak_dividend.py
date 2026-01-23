import akshare as ak

def test_gxl():
    print("Testing stock_a_gxl_lg...")
    try:
        # Check if it accepts symbol or returns all
        # Usually lg interfaces return all or rank.
        df = ak.stock_a_gxl_lg(symbol="000001")
        if df is not None:
             print("stock_a_gxl_lg result:")
             print(list(df.columns))
             print(df.tail(1))
        else:
            print("stock_a_gxl_lg returned None")
    except Exception as e:
        print(f"stock_a_gxl_lg error: {e}")
        
    print("\nTesting stock_hk_gxl_lg...")
    try:
        df_hk = ak.stock_hk_gxl_lg()
        if df_hk is not None:
             print("stock_hk_gxl_lg (All) result columns:")
             print(list(df_hk.columns))
             print(df_hk.head(1))
        else:
            print("stock_hk_gxl_lg returned None")
    except Exception as e:
        print(f"stock_hk_gxl_lg error: {e}")

if __name__ == "__main__":
    test_gxl()
