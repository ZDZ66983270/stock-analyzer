import os
import urllib.request
import requests
import sys

def check():
    print("--- Environment Variables ---")
    for k in ['http_proxy', 'https_proxy', 'all_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY']:
        print(f"{k}: {os.environ.get(k)}")

    print("\n--- urllib.request.getproxies() ---")
    # This checks system registry/config on Mac/Windows if env vars are empty
    proxies = urllib.request.getproxies()
    print(proxies)

    print("\n--- Testing Requests (Default) ---")
    try:
        r = requests.get("https://www.baidu.com", timeout=5)
        print(f"Baidu Default: {r.status_code}")
    except Exception as e:
        print(f"Baidu Default Failed: {e}")

    print("\n--- Testing Requests (Trust Env=False) ---")
    try:
        s = requests.Session()
        s.trust_env = False
        r = s.get("https://www.baidu.com", timeout=5)
        print(f"Baidu No-Env: {r.status_code}")
    except Exception as e:
        print(f"Baidu No-Env Failed: {e}")

if __name__ == "__main__":
    check()
