import akshare as ak
import pandas as pd
import sys
import os
sys.path.append(os.getcwd())
from database import engine
from sqlmodel import Session, select
from models import Watchlist

def test_interfaces():
    print("--- 正在加载自选股列表 ---")
    watchlist_symbols = []
    try:
        with Session(engine) as session:
            wl = session.exec(select(Watchlist)).all()
            watchlist_symbols = [(w.symbol, w.market) for w in wl]
    except Exception as e:
        print(f"DB Error: {e}")
        # Fallback manual list if DB fails
        watchlist_symbols = [('09988.hk', 'HK'), ('00005.hk', 'HK'), ('600519.sh', 'CN'), ('600309.sh', 'CN')]
    
    print(f"自选股: {watchlist_symbols}")
    
    # helper to clean symbol
    def clean_symbol(s): 
        return s.split('.')[0]

    target_hk = [clean_symbol(s[0]) for s in watchlist_symbols if s[1] == 'HK']
    target_cn = [clean_symbol(s[0]) for s in watchlist_symbols if s[1] == 'CN']
    
    print("\n--- 1. 测试 A+H 股实时行情 (stock_zh_ah_spot_em) ---")
    try:
        ah_df = ak.stock_zh_ah_spot_em()
        # Columns: 序号, 名称, H股代码, 最新价-HKD, H股-涨跌幅, A股代码, ...
        # Join targets
        found = False
        for _, row in ah_df.iterrows():
            h_code = str(row['H股代码'])
            a_code = str(row['A股代码'])
            
            if h_code in target_hk or a_code in target_cn:
                found = True
                print(f"Found A+H Match: {row['名称']} | H:{h_code} (${row['最新价-HKD']}, {row['H股-涨跌幅']}%) | A:{a_code} (¥{row['最新价-RMB']}, {row['A股-涨跌幅']}%)")
        
        if not found:
            print("自选股中没有属于 'A+H股' 板块的标的。")
            
    except Exception as e:
        print(f"A+H 接口报错: {e}")

    print("\n--- 2. 测试 港股 实时行情 (stock_hk_spot_em) ---")
    try:
        if target_hk:
            print("Fetching HK Spot...")
            hk_df = ak.stock_hk_spot_em()
            # Columns: 序号, 名称, 代码, 最新价, 涨跌额, 涨跌幅, ...
            for _, row in hk_df.iterrows():
                code = str(row['代码'])
                if code in target_hk:
                    print(f"HK Spot: {row['名称']} ({code}) | Price: {row['最新价']} | Change: {row['涨跌幅']}%")
        else:
            print("无港股自选，跳过。")
    except Exception as e:
        print(f"港股接口报错: {e}")

    print("\n--- 3. 测试 A股 实时行情 (stock_zh_a_spot_em) ---")
    try:
        if target_cn:
            print("fetching full A-share spot (~5000 rows)...")
            cn_df = ak.stock_zh_a_spot_em()
            for _, row in cn_df.iterrows():
                code = str(row['代码'])
                if code in target_cn:
                     print(f"CN Spot: {row['名称']} ({code}) | Price: {row['最新价']} | Change: {row['涨跌幅']}%")
        else:
             print("无A股自选，跳过。")
    except Exception as e:
        print(f"A股接口报错: {e}")

if __name__ == "__main__":
    test_interfaces()
