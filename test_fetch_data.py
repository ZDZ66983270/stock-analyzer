import akshare as ak
from datetime import datetime, timedelta
import pandas as pd
import time

def format_date(date_str):
    """格式化日期字符串"""
    return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"

def test_fetch_data():
    """
    测试数据获取功能
    """
    # 设置测试日期范围（使用实际的历史日期）
    end_date = '20240426'  # 使用最近的实际交易日
    start_date = '20240419'  # 一周前
    
    # 格式化日期
    formatted_start = format_date(start_date)
    formatted_end = format_date(end_date)
    
    # 测试用例：不同市场的股票
    test_cases = [
        ('sh601318', 'A股-中国平安'),
        ('sz000001', 'A股-平安银行'),
        ('00700', '港股-腾讯控股'),
        ('09988', '港股-阿里巴巴'),
        ('AAPL', '美股-苹果'),
        ('MSFT', '美股-微软'),
        ('GOOGL', '美股-谷歌'),
        ('NVDA', '美股-英伟达')
    ]
    
    print(f"\n开始测试数据获取功能...")
    print(f"测试时间范围: {formatted_start} 至 {formatted_end}\n")
    
    for symbol, description in test_cases:
        print(f"测试 {description} ({symbol}):")
        retries = 3
        success = False
        
        while retries > 0 and not success:
            try:
                # 使用akshare获取数据
                if symbol.startswith(('sh', 'sz')):
                    # A股数据
                    data = ak.stock_zh_a_hist(
                        symbol=symbol[2:],
                        start_date=start_date,
                        end_date=end_date,
                        adjust="qfq"
                    )
                    # 重命名列以统一格式
                    data = data.rename(columns={
                        '日期': 'Date',
                        '开盘': 'Open',
                        '收盘': 'Close',
                        '最高': 'High',
                        '最低': 'Low',
                        '成交量': 'Volume',
                        '成交额': 'Amount'
                    })
                elif symbol.startswith(('0', '1', '2', '3', '6')):
                    # 港股数据
                    data = ak.stock_hk_hist(
                        symbol=symbol,
                        period="daily",
                        adjust=""
                    )
                    # 将日期列转换为datetime
                    data['日期'] = pd.to_datetime(data['日期']).dt.date
                    # 过滤日期范围
                    start_dt = datetime.strptime(formatted_start, '%Y-%m-%d').date()
                    end_dt = datetime.strptime(formatted_end, '%Y-%m-%d').date()
                    data = data[
                        (data['日期'] >= start_dt) &
                        (data['日期'] <= end_dt)
                    ]
                    # 重命名列以统一格式
                    data = data.rename(columns={
                        '日期': 'Date',
                        '开盘': 'Open',
                        '收盘': 'Close',
                        '最高': 'High',
                        '最低': 'Low',
                        '成交量': 'Volume',
                        '成交额': 'Amount'
                    })
                else:
                    # 美股数据
                    data = ak.stock_us_daily(
                        symbol=symbol,
                        adjust="qfq"
                    )
                    # 将日期索引转换为列
                    data = data.reset_index()
                    # 将日期列转换为datetime
                    data['date'] = pd.to_datetime(data['date']).dt.date
                    # 过滤日期范围
                    start_dt = datetime.strptime(formatted_start, '%Y-%m-%d').date()
                    end_dt = datetime.strptime(formatted_end, '%Y-%m-%d').date()
                    data = data[
                        (data['date'] >= start_dt) &
                        (data['date'] <= end_dt)
                    ]
                    # 重命名列以统一格式
                    data = data.rename(columns={
                        'date': 'Date',
                        'open': 'Open',
                        'close': 'Close',
                        'high': 'High',
                        'low': 'Low',
                        'volume': 'Volume'
                    })
                    # 添加成交额列（美股数据可能没有）
                    if 'Amount' not in data.columns:
                        data['Amount'] = data['Volume'] * data['Close']
                
                if data is not None and not data.empty:
                    print(f"✓ 成功获取数据")
                    print(f"  - 数据点数量: {len(data)}")
                    print(f"  - 数据字段: {', '.join(data.columns)}")
                    print(f"  - 数据日期范围: {data['Date'].iloc[0]} 至 {data['Date'].iloc[-1]}")
                    print(f"  - 最新收盘价: {data['Close'].iloc[-1]:.2f}")
                    print(f"  - 最新成交量: {int(data['Volume'].iloc[-1])}")
                    success = True
                else:
                    print(f"✗ 第 {4-retries} 次尝试：未能获取数据")
                    retries -= 1
                    
            except Exception as e:
                print(f"✗ 第 {4-retries} 次尝试出错: {str(e)}")
                retries -= 1
                if retries > 0:
                    print("等待5秒后重试...")
                    time.sleep(5)
            
        if not success:
            print("❌ 所有重试都失败")
        print()

if __name__ == '__main__':
    test_fetch_data() 