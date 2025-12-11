import pandas as pd
import numpy as np
from modules.technical_indicators import add_technical_indicators

# 创建测试数据
def create_test_data():
    dates = pd.date_range(start='2024-01-01', periods=100)
    np.random.seed(42)
    data = {
        'OPEN': np.random.normal(100, 5, 100),
        'HIGH': np.random.normal(105, 5, 100),
        'LOW': np.random.normal(95, 5, 100),
        'CLOSE': np.random.normal(100, 5, 100),
        'VOLUME': np.random.randint(1000000, 10000000, 100)
    }
    df = pd.DataFrame(data, index=dates)
    return df

# 测试技术指标计算
def test_indicators():
    # 创建测试数据
    df = create_test_data()
    print("原始数据:")
    print(df.head())
    
    # 计算技术指标
    df_with_indicators = add_technical_indicators(df)
    
    # 打印结果
    print("\n计算后的技术指标:")
    print(df_with_indicators[['MA5', 'MA10', 'MA20', 'DIF', 'DEA', 'MACD', 'K', 'D', 'J', 'RSI6', 'RSI12', 'RSI24']].head())

if __name__ == '__main__':
    test_indicators() 