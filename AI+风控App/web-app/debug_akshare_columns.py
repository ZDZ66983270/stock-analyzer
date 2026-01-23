import akshare as ak
import pandas as pd

def check_cn():
    print("--- Checking CN YJBB (Summary) ---")
    try:
        df = ak.stock_yjbb_em(date="20240331")
        if df is not None and not df.empty:
            print(f"Columns: {df.columns.tolist()[:10]} ...")
            if '每股收益' in df.columns:
                print("✅ Found '每股收益'")
            else:
                print("❌ '每股收益' NOT found")
    except Exception as e:
        print(f"Error: {e}")

def check_hk():
    print("\n--- Checking HK Financial Analysis ---")
    try:
        # Tencent
        df = ak.stock_financial_hk_analysis_indicator_em(symbol="00700", indicator="年度")
        if df is not None and not df.empty:
            print(f"Columns: {df.columns.tolist()[:10]} ...")
            # Look for EPS related
            possible = [c for c in df.columns if 'EPS' in c.upper() or 'EARN' in c.upper() or '每股' in c]
            print(f"Potential EPS columns: {possible}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_cn()
    check_hk()
