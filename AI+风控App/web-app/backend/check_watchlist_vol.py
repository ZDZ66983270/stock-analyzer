
import requests

try:
    resp = requests.get("http://127.0.0.1:8000/api/watchlist")
    data = resp.json() # Direct list
    print("=== Watchlist Volume Check ===")
    if isinstance(data, list):
        for item in data:
            vol = item.get('volume')
            print(f"Symbol: {item['symbol']} | Vol: {vol} ({type(vol)})")
    else:
        print(f"Response not a list: {data}")
except Exception as e:
    print(f"Error: {e}")
