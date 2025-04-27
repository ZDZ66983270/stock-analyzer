import pandas as pd
import os
from typing import Dict, Optional
import logging
from config import OUTPUT_DIR, INDICATOR_SETTINGS, CSV_COLUMNS, ALL_COLUMNS
from utils.indicator_calculator import IndicatorCalculator

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def merge_kline_data(kline_data: Dict[str, pd.DataFrame], period: str = '1d') -> Optional[pd.DataFrame]:
    """
    合并不同周期的K线数据到日线周期
    
    Args:
        kline_data: 不同周期的K线数据字典
        period: 目标周期，默认为日线
        
    Returns:
        Optional[pd.DataFrame]: 合并后的K线数据
    """
    try:
        if period not in kline_data:
            logging.error(f"未找到{period}周期的K线数据")
            return None
        
        # 使用目标周期的数据作为基准
        base_df = kline_data[period]
        
        # 确保时间列格式正确
        base_df['time'] = pd.to_datetime(base_df['time'])
        
        return base_df
        
    except Exception as e:
        logging.error(f"合并K线数据时发生错误: {str(e)}")
        return None

def calculate_indicators(kline_data: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    计算技术指标
    
    Args:
        kline_data: K线数据
        
    Returns:
        Optional[pd.DataFrame]: 包含技术指标的数据
    """
    try:
        return IndicatorCalculator.calculate_all_indicators(
            kline_data,
            ma_periods=INDICATOR_SETTINGS['MA'],
            rsi_periods=INDICATOR_SETTINGS['RSI'],
            macd_settings=INDICATOR_SETTINGS['MACD'],
            kdj_settings=INDICATOR_SETTINGS['KDJ']
        )
    except Exception as e:
        logging.error(f"计算技术指标时发生错误: {str(e)}")
        return None

def merge_with_capital_flow(data: pd.DataFrame, capital_flow: pd.DataFrame) -> pd.DataFrame:
    """
    合并K线和资金流数据
    
    Args:
        data: K线和技术指标数据
        capital_flow: 资金流数据
        
    Returns:
        pd.DataFrame: 合并后的数据
    """
    try:
        # 确保时间列格式一致
        data['time'] = pd.to_datetime(data['time'])
        capital_flow['time'] = pd.to_datetime(capital_flow['time'])
        
        # 合并数据
        merged = pd.merge(data, capital_flow, on='time', how='left')
        
        # 填充缺失的资金流数据
        flow_columns = CSV_COLUMNS['capital_flow']
        merged[flow_columns] = merged[flow_columns].fillna(0)
        
        return merged
        
    except Exception as e:
        logging.error(f"合并资金流数据时发生错误: {str(e)}")
        return data

def save_to_csv(data: pd.DataFrame, symbol: str) -> bool:
    """
    保存数据到CSV文件
    
    Args:
        data: 要保存的数据
        symbol: 股票代码
        
    Returns:
        bool: 是否保存成功
    """
    try:
        # 创建输出目录
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # 构建文件名
        filename = f"{symbol.replace('.', '_')}.csv"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        # 确保所有必要的列都存在
        for col in ALL_COLUMNS:
            if col not in data.columns:
                data[col] = 0
        
        # 按照指定列顺序保存
        data[ALL_COLUMNS].to_csv(filepath, index=False)
        logging.info(f"数据已保存到 {filepath}")
        return True
        
    except Exception as e:
        logging.error(f"保存数据到CSV时发生错误: {str(e)}")
        return False

def merge_all_data(symbol: str,
                   kline_data: Dict[str, pd.DataFrame],
                   capital_flow: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    合并所有数据的主函数
    
    Args:
        symbol: 股票代码
        kline_data: K线数据字典
        capital_flow: 资金流数据
        
    Returns:
        Optional[pd.DataFrame]: 合并后的数据
    """
    try:
        # 1. 合并K线数据
        base_data = merge_kline_data(kline_data)
        if base_data is None:
            return None
        
        # 2. 计算技术指标
        with_indicators = calculate_indicators(base_data)
        if with_indicators is None:
            return None
        
        # 3. 合并资金流数据
        final_data = merge_with_capital_flow(with_indicators, capital_flow)
        
        # 4. 保存数据
        if save_to_csv(final_data, symbol):
            return final_data
        return None
        
    except Exception as e:
        logging.error(f"合并数据时发生错误: {str(e)}")
        return None

if __name__ == "__main__":
    # 测试代码
    # 创建示例数据
    test_kline = {
        '1d': pd.DataFrame({
            'time': pd.date_range(start='2024-01-01', periods=10),
            'open': [100] * 10,
            'high': [105] * 10,
            'low': [95] * 10,
            'close': [102] * 10,
            'volume': [1000] * 10
        })
    }
    
    test_capital_flow = pd.DataFrame({
        'time': pd.date_range(start='2024-01-01', periods=10),
        'capital_inflow': [1000] * 10,
        'capital_outflow': [800] * 10,
        'capital_netflow': [200] * 10
    })
    
    try:
        result = merge_all_data('US.TEST', test_kline, test_capital_flow)
        if result is not None:
            print("\n合并结果示例：")
            print(result.head())
    except Exception as e:
        print(f"测试失败: {str(e)}") 