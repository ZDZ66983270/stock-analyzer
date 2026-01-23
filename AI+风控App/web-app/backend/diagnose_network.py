import requests
import os
import sys

URL = "https://push2his.eastmoney.com/api/qt/stock/trends2/get?fields1=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13&fields2=f51,f52,f53,f54,f55,f56,f57,f58&ut=7eea3edcaed734bea9cbfc24409ed989&ndays=1&iscr=0&secid=1.600036"

def test_connect():
    print(f"Testing URL: {URL}")
    
    # Test 1: Default
    print("\n--- Test 1: Default Requests ---")
    try:
        r = requests.get(URL, timeout=5)
        print(f"Status: {r.status_code}")
        print("Success! (Default)")
    except Exception as e:
        print(f"Failed: {e}")

    # Test 2: No Proxy Env
    print("\n--- Test 2: Clear Proxy Env ---")
    old_env = {}
    for k in ['http_proxy', 'https_proxy', 'all_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY']:
        if k in os.environ:
            old_env[k] = os.environ[k]
            del os.environ[k]
    
    try:
        r = requests.get(URL, timeout=5)
        print(f"Status: {r.status_code}")
        print("Success! (Env Cleared)")
    except Exception as e:
        print(f"Failed: {e}")
    finally:
        os.environ.update(old_env) # Restore

    # Test 3: Session trust_env=False
    print("\n--- Test 3: Session(trust_env=False) ---")
    try:
        s = requests.Session()
        s.trust_env = False
        r = s.get(URL, timeout=5)
        print(f"Status: {r.status_code}")
        print("Success! (trust_env=False)")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_connect()
