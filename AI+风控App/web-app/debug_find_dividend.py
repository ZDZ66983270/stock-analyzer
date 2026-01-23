
import akshare as ak

def find_dividend_functions():
    print("Searching for dividend-related functions in AkShare...")
    candidates = []
    for attr in dir(ak):
        if 'dividend' in attr.lower() or 'fenhong' in attr.lower() or 'fhps' in attr.lower():
            candidates.append(attr)
    print("Found candidates:", candidates)

    # Let's test likely ones
    # stock_fhps_detail_em: 分红配送
    if 'stock_fhps_detail_em' in candidates:
        print("\nTesting stock_fhps_detail_em for 600030:")
        try:
            df = ak.stock_fhps_detail_em(symbol="600030")
            print(df.head() if df is not None else "None")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    find_dividend_functions()
