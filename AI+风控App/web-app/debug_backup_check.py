
import requests
import pandas as pd
import akshare as ak

def test_baidu_ashare(code):
    print(f"Testing Baidu OpenData for A-share {code}...")
    url = "https://gushitong.baidu.com/opendata"
    # Try market='ab' (A/B share?) or 'cn'
    params = {
        "openapi": "1",
        "dspName": "iphone",
        "tn": "tangram",
        "client": "app",
        "query": "股息率",
        "code": code,
        "resource_id": "51171",
        "srcid": "51171",
        "market": "ab", # Guessing
        "tag": "股息率",
        "skip_industry": "1",
        "chart_select": "全部",
        "finClientType": "pc"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            # Just print the structure to see if we got data
            if data.get("Result"):
                print("Result found!")
                # check body
                try:
                    display = data['Result'][0]['DisplayData']['resultData']['tplData']['result']
                    chart = display['chartInfo'][0]['body']
                    print(f"Data points found: {len(chart)}")
                    print("Sample:", chart[:2])
                except:
                    print("Could not parse detailed structure.")
            else:
                print("No Result in response.")
    except Exception as e:
        print(f"Baidu Error: {e}")

def test_financial_abstract(symbol):
    print(f"\nTesting ak.stock_financial_abstract(symbol='{symbol}')...")
    try:
        df = ak.stock_financial_abstract(symbol=symbol)
        if df is not None:
             print("Columns:", df.columns.tolist())
             print(df.head())
        else:
            print("No data.")
    except Exception as e:
        print(f"Abstract Error: {e}")

if __name__ == "__main__":
    test_baidu_ashare("600030")
    test_financial_abstract("600030")
