import akshare as ak

def list_hk_apis():
    print("Searching for HK related functions in AkShare...")
    all_attrs = dir(ak)
    hk_apis = [a for a in all_attrs if 'hk' in a.lower() and ('financial' in a.lower() or 'sheet' in a.lower() or 'cash' in a.lower() or 'profit' in a.lower())]
    
    for api in hk_apis:
        print(f"Found: {api}")

if __name__ == "__main__":
    list_hk_apis()
