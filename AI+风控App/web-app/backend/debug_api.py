import requests
import json
import os

# Disable proxy for localhost testing
os.environ['NO_PROXY'] = '127.0.0.1,localhost'
for k in ['http_proxy', 'https_proxy', 'all_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY']:
    if k in os.environ:
        del os.environ[k]

def test_watchlist_api():
    try:
        response = requests.get("http://127.0.0.1:8000/api/watchlist")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            # Print first item to check structure
            if data and len(data) > 0:
                print("First item sample:")
                print(json.dumps(data[0], indent=2, ensure_ascii=False))
            else:
                print("Watchlist is empty.")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    test_watchlist_api()
