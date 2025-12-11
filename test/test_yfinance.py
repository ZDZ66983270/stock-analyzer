import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import logging

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def test_yfinance_data():
    """测试雅虎财经数据获取能力"""
    logger = setup_logging()
    
    # 测试股票列表
    test_stocks = {
        "HK": ["0700.HK", "0941.HK"],  # 腾讯控股，中国移动
        "US": ["AAPL", "MSFT"]         # 苹果，微软
    }
    
    # 测试周期
    test_periods = {
        "daily": "1d",
        "weekly": "1wk",
        "monthly": "1mo",
        "hourly": "1h",
        "30min": "30m",
        "15min": "15m",
        "5min": "5m"
    }
    
    # 测试时间范围 - 使用更近的时间
    end_date = datetime.now()
    test_ranges = {
        "short": (end_date - timedelta(days=1), end_date),    # 1天
        "medium": (end_date - timedelta(days=7), end_date),   # 7天
        "long": (end_date - timedelta(days=30), end_date)     # 30天
    }
    
    results = []
    
    for market, symbols in test_stocks.items():
        for symbol in symbols:
            for period_name, interval in test_periods.items():
                for range_name, (start_date, end_date) in test_ranges.items():
                    try:
                        logger.info(f"测试 {symbol} {period_name} {range_name}")
                        
                        # 获取数据
                        ticker = yf.Ticker(symbol)
                        df = ticker.history(
                            start=start_date,
                            end=end_date,
                            interval=interval
                        )
                        
                        # 记录结果
                        result = {
                            "market": market,
                            "symbol": symbol,
                            "period": period_name,
                            "range": range_name,
                            "success": not df.empty,
                            "rows": len(df),
                            "columns": list(df.columns),
                            "start_date": df.index[0] if not df.empty else None,
                            "end_date": df.index[-1] if not df.empty else None
                        }
                        
                        results.append(result)
                        logger.info(f"结果: {result}")
                        
                        # 保存数据
                        if not df.empty:
                            save_path = os.path.join("test_data", "yfinance", market, period_name)
                            os.makedirs(save_path, exist_ok=True)
                            filename = f"{symbol}_{period_name}_{range_name}.csv"
                            df.to_csv(os.path.join(save_path, filename))
                            
                    except Exception as e:
                        logger.error(f"测试失败: {symbol} {period_name} {range_name} - {str(e)}")
                        results.append({
                            "market": market,
                            "symbol": symbol,
                            "period": period_name,
                            "range": range_name,
                            "success": False,
                            "error": str(e)
                        })
    
    # 保存测试结果
    results_df = pd.DataFrame(results)
    results_df.to_csv("test_data/yfinance_test_results.csv", index=False)
    logger.info("测试完成，结果已保存")

if __name__ == "__main__":
    test_yfinance_data() 