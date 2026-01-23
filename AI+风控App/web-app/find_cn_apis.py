import akshare as ak

def list_cn_apis():
    print("Searching for CN related functions in AkShare...")
    all_attrs = dir(ak)
    # Look for common pinyin: zcfz (balance sheet), xjll (cash flow), lrb (income statement)
    cn_apis = [a for a in all_attrs if 'zcfz' in a or 'xjll' in a or 'lrb' in a]
    
    for api in cn_apis:
        if 'em' in api: # Prioritize EastMoney interfaces
            print(f"Found: {api}")

if __name__ == "__main__":
    list_cn_apis()
