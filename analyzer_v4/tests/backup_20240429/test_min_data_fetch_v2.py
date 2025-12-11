from modules.min_data_fetcher import fetch_hk_min_data, fetch_us_min_data, save_minute_data_to_csv

def test_fetch_hk_minute_data():
    symbol = "09988"  # 阿里巴巴港股代码
    df_hk = fetch_hk_min_data(symbol=symbol, period='1')
    print(df_hk.head())
    save_minute_data_to_csv(df_hk, f"./output/{symbol}_hk_minute_data.csv")

def test_fetch_us_minute_data():
    symbol = "105.MSFT"  # 微软美股代码
    df_us = fetch_us_min_data(symbol=symbol)
    print(df_us.head())
    save_minute_data_to_csv(df_us, f"./output/{symbol}_us_minute_data.csv")

if __name__ == "__main__":
    print("="*60)
    test_fetch_hk_minute_data()
    print("="*60)
    test_fetch_us_minute_data()
    print("="*60) 