
import requests

FMP_API_KEY = "yytaAKONtPbR5cBcx9azLeqlovaWDRQm"

def test_fmp_raw():
    symbol = "AAPL"
    url = f"https://financialmodelingprep.com/api/v3/income-statement/{symbol}?apikey={FMP_API_KEY}&limit=1"
    print(f"🔬 Testing Raw URL: {url.replace(FMP_API_KEY, 'HIDDEN')}")
    
    try:
        res = requests.get(url, timeout=10)
        print(f"Status Code: {res.status_code}")
        print(f"Response: {res.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_fmp_raw()
