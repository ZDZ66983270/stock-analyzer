import os
from modules.data_fetcher import DataFetcher

def test_data_fetcher():
    # 创建数据获取器
    fetcher = DataFetcher(data_dir="test_data")
    
    # 测试A股
    a_stocks = [
        "000001.SZ",  # 平安银行
        "600000.SH",  # 浦发银行
    ]
    
    # 测试港股
    hk_stocks = [
        "0700.HK",  # 腾讯控股
        "0941.HK",  # 中国移动
    ]
    
    # 测试美股
    us_stocks = [
        "AAPL",   # 苹果
        "MSFT",   # 微软
    ]
    
    # 获取A股数据
    print("\n获取A股数据...")
    fetcher.batch_fetch(
        market="a",
        symbols=a_stocks,
        start_date="2024-01-01",
        end_date="2024-03-20",
        freqs=["daily", "5min"]
    )
    
    # 获取港股数据
    print("\n获取港股数据...")
    fetcher.batch_fetch(
        market="hk",
        symbols=hk_stocks,
        start_date="2024-01-01",
        end_date="2024-03-20",
        freqs=["daily", "5min"]
    )
    
    # 获取美股数据
    print("\n获取美股数据...")
    fetcher.batch_fetch(
        market="us",
        symbols=us_stocks,
        start_date="2024-01-01",
        end_date="2024-03-20",
        freqs=["daily", "5min"]
    )

if __name__ == "__main__":
    test_data_fetcher() 