import os
import pandas as pd
import akshare as ak
from datetime import datetime, timedelta
import logging

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def test_akshare_data():
    """测试 akshare 数据获取能力"""
    logger = setup_logging()
    
    # 测试股票列表
    test_stocks = {
        "A": {
            "000001.SZ": "平安银行",
            "600000.SH": "浦发银行"
        },
        "HK": {
            "00700": "腾讯控股",
            "00941": "中国移动"
        },
        "US": {
            "AAPL": "苹果",
            "MSFT": "微软"
        }
    }
    
    # 测试周期
    test_periods = {
        "daily": "daily",
        "weekly": "weekly",
        "monthly": "monthly",
        "5min": "5",
        "15min": "15",
        "30min": "30",
        "60min": "60"
    }
    
    results = []
    
    for market, stocks in test_stocks.items():
        for code, name in stocks.items():
            for period_name, period in test_periods.items():
                try:
                    logger.info(f"测试 {market} {code} {name} {period_name}")
                    
                    # 获取数据
                    if market == "A":
                        if period_name in ["daily", "weekly", "monthly"]:
                            df = ak.stock_zh_a_hist(symbol=code, period=period_name, adjust="qfq")
                        else:
                            df = ak.stock_zh_a_hist_min_em(symbol=code, period=period)
                            
                    elif market == "HK":
                        if period_name in ["daily", "weekly", "monthly"]:
                            df = ak.stock_hk_daily(symbol=code)
                        else:
                            df = ak.stock_hk_hist_min_em(symbol=code, period=period)
                            
                    elif market == "US":
                        if period_name in ["daily", "weekly", "monthly"]:
                            df = ak.stock_us_daily(symbol=code)
                        else:
                            df = ak.stock_us_hist_min_em(symbol=code, period=period)
                    
                    # 记录结果
                    result = {
                        "market": market,
                        "code": code,
                        "name": name,
                        "period": period_name,
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
                        save_path = os.path.join("test_data", "akshare", market, period_name)
                        os.makedirs(save_path, exist_ok=True)
                        filename = f"{code}_{period_name}.csv"
                        df.to_csv(os.path.join(save_path, filename))
                        
                except Exception as e:
                    logger.error(f"测试失败: {market} {code} {period_name} - {str(e)}")
                    results.append({
                        "market": market,
                        "code": code,
                        "name": name,
                        "period": period_name,
                        "success": False,
                        "error": str(e)
                    })
    
    # 保存测试结果
    results_df = pd.DataFrame(results)
    results_df.to_csv("test_data/akshare_test_results.csv", index=False)
    logger.info("测试完成，结果已保存")

if __name__ == "__main__":
    test_akshare_data() 