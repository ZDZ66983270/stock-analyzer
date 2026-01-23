import akshare as ak
import pandas as pd

def test_hk_financial():
    # Test with 00700 (Tencent) from symbols.txt
    symbol = "00700"
    print(f"--- Testing HK Stock Financial Data for {symbol} ---")
    
    try:
        print("\n1. Using stock_financial_hk_analysis_indicator_em (AkShare)")
        df = ak.stock_financial_hk_analysis_indicator_em(symbol=symbol, indicator="年度")
        if df is not None and not df.empty:
            print(f"✅ Annual Data Success! Shape: {df.shape}")
            print(f"   Columns: {df.columns.tolist()[:10]} ...")
            
            # Check for EPS
            eps_cols = [c for c in df.columns if 'EPS' in c.upper() or '每股' in c]
            print(f"   EPS Columns: {eps_cols}")
            
            # Show sample
            if 'BASIC_EPS' in df.columns and 'REPORT_DATE' in df.columns:
                print(f"\n   Sample Data:")
                print(df[['REPORT_DATE', 'BASIC_EPS', 'DILUTED_EPS']].head(3))
        else:
            print("   ❌ Returned empty.")
            
        # Try Quarterly
        print("\n2. Trying Quarterly Data (季度)")
        df_q = ak.stock_financial_hk_analysis_indicator_em(symbol=symbol, indicator="季度")
        if df_q is not None and not df_q.empty:
            print(f"✅ Quarterly Data Success! Shape: {df_q.shape}")
            if 'BASIC_EPS' in df_q.columns and 'REPORT_DATE' in df_q.columns:
                print(f"\n   Sample Quarterly Data:")
                print(df_q[['REPORT_DATE', 'BASIC_EPS']].head(4))
        else:
            print("   ❌ Quarterly data empty.")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_hk_financial()
