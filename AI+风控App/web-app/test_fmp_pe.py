
import sys
import requests
import pandas as pd

FMP_API_KEY = "yytaAKONtPbR5cBcx9azLeqlovaWDRQm"

def test_fetch_annual():
    print("\n--- Testing Annual (Limit=5) ---")
    url = f"https://financialmodelingprep.com/stable/ratios?symbol=TSLA&period=annual&limit=5&apikey={FMP_API_KEY}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if data:
            df = pd.DataFrame(data)
            print(df[['date', 'priceToEarningsRatio', 'priceToBookRatio']].head())
        else:
            print("No Data")
    except Exception as e:
        print(f"Error: {e}")

def test_fetch_quarterly():
    print("\n--- Testing Quarterly (Limit=5) ---")
    url = f"https://financialmodelingprep.com/stable/ratios?symbol=TSLA&period=quarter&limit=5&apikey={FMP_API_KEY}"
    try:
        resp = requests.get(url, timeout=10)
        print(f"Response Code: {resp.status_code}")
        try:
            data = resp.json()
            # Check if error or data
            if isinstance(data, dict) and 'Error Message' in data:
                print(f"API Error: {data['Error Message']}")
            elif data:
                df = pd.DataFrame(data)
                print(df[['date', 'priceToEarningsRatio', 'priceToBookRatio']].head())
            else:
                print("No Data")
        except:
            print(f"Response Text: {resp.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # test_fetch_annual()
    test_fetch_quarterly()
