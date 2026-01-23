from fetch_financials import fetch_akshare_hk_financials
import logging

# Suppress Logs
logging.basicConfig(level=logging.ERROR)

def test_hk_logic():
    print("Testing 00700.HK...")
    res = fetch_akshare_hk_financials("00700.HK")
    if not res:
        print("Empty result")
    else:
        print(f"Found {len(res)} records.")
        for r in res:
            print(f"   Date: {r['as_of_date']} Revenue: {r['revenue_ttm']}")

if __name__ == "__main__":
    test_hk_logic()
