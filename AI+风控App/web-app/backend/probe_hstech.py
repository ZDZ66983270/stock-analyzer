
import requests
import akshare as ak

def check_sina():
    codes = [
        "hk800700", "rt_hk800700", "hkHSTECH", "rt_hkHSTECH", "HSTECH",
        "hk800000", "rt_hkHSI", "hkHSI"
    ]
    print("--- Sina Probe ---")
    for c in codes:
        url = f"http://hq.sinajs.cn/list={c}"
        try:
            r = requests.get(url, headers={"Referer": "http://finance.sina.com.cn/"}, timeout=2)
            print(f"{c}: {r.text.strip()}")
        except Exception as e:
            print(f"{c}: Error {e}")

def check_tencent():
    codes = ["hk800700", "r_hk800700", "s_hk800700", "hkHSTECH"]
    print("\n--- Tencent Probe ---")
    for c in codes:
        url = f"http://qt.gtimg.cn/q={c}"
        try:
            r = requests.get(url, timeout=2)
            print(f"{c}: {r.text.strip()}")
        except:
            pass

def check_akshare():
    print("\n--- AkShare Probe ---")
    try:
        # daily
        df = ak.stock_hk_index_daily_sina(symbol="HSTECH")
        print(f"Sina Daily HSTECH: {len(df) if df is not None else 0} rows")
    except Exception as e:
        print(f"Sina Daily HSTECH error: {e}")

    try:
        # EM Spot for index?
        # EM doesn't distinguish much between stock and index in code sometimes
        df = ak.stock_hk_hist_min_em(symbol="800700", period="1")
        print(f"EM Min 800700: {len(df) if df is not None else 0} rows")
    except Exception as e:
        print(f"EM Min 800700 error: {e}")

if __name__ == "__main__":
    check_sina()
    check_tencent()
    check_akshare()
