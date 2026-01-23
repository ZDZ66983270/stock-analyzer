import requests
import json

def probe_watchlist():
    url = "http://127.0.0.1:8000/api/watchlist"
    print(f"GET {url}...")
    try:
        resp = requests.get(url, timeout=5)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"Count: {len(data)}")
            print(f"Data: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"Error Body: {resp.text}")
    except Exception as e:
        print(f"Request Failed: {e}")

if __name__ == "__main__":
    probe_watchlist()
