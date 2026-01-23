import requests

def test_smartbox():
    q = "中远海控"
    url = f"http://smartbox.gtimg.cn/s3/?q={q}&t=all"
    print(f"Testing URL: {url}")
    try:
        resp = requests.get(url, timeout=5)
        print(f"Status: {resp.status_code}")
        print("Content:")
        print(resp.text)
        
        content = resp.text
        if 'v_hint="' in content:
            raw_data = content.split('v_hint="')[1].split('"')[0]
            items = raw_data.split('^')
            for i, item in enumerate(items):
                print(f"Item {i}: {item}")
                parts = item.split('~')
                print(f"  Parts: {parts}")
                if len(parts) >= 4:
                    print(f"  Code: {parts[0]}")
                    print(f"  Name: {parts[1]}")
                    print(f"  Market: {parts[3]}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_smartbox()
