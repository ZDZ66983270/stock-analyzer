
import requests

def test_tencent_search(q):
    url = f"http://smartbox.gtimg.cn/s3/?q={q}&t=all"
    print(f"Querying: {url}")
    try:
        resp = requests.get(url, timeout=5)
        print(f"Status: {resp.status_code}")
        print(f"Content: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_tencent_search("TSLA")
    test_tencent_search("600519")
    test_tencent_search("00700")
