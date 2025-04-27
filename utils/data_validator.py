import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Tuple
import logging
from datetime import datetime, timedelta

class DataValidator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 定义必需的基础列
        self.required_columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
        
        # 定义各指标所需的最小数据点数
        self.min_data_points = {
            'MA': 20,  # 最长的MA周期为20
            'MACD': 26,  # MACD需要26天数据
            'KDJ': 9,  # KDJ需要9天数据
            'RSI': 24  # 最长的RSI周期为24
        }
        
        # 定义价格和成交量的合理范围
        self.price_limits = {
            'min': 0.01,  # 最小价格
            'max': 1000000  # 最大价格
        }
        self.volume_limits = {
            'min': 0,  # 最小成交量
            'max': 1000000000000  # 最大成交量（1万亿）
        }

    def validate_data(self, 
                     df: pd.DataFrame, 
                     period: str) -> Tuple[bool, Optional[str]]:
        """
        验证数据完整性
        
        Args:
            df: 待验证的DataFrame
            period: 数据周期
            
        Returns:
            Tuple[bool, Optional[str]]: (是否通过验证, 错误信息)
        """
        try:
            # 1. 检查DataFrame是否为空
            if df is None or df.empty:
                return False, f"{period}周期数据为空"
            
            # 2. 检查必需列是否存在
            missing_cols = [col for col in self.required_columns if col not in df.columns]
            if missing_cols:
                return False, f"{period}周期数据缺少必需列: {', '.join(missing_cols)}"
            
            # 3. 检查数据类型
            if not self._validate_data_types(df):
                return False, f"{period}周期数据类型错误"
            
            # 4. 检查数据点数量是否满足计算指标的要求
            min_required = max(self.min_data_points.values())
            if len(df) < min_required:
                return False, f"{period}周期数据点数量不足，需要至少{min_required}个数据点"
            
            # 5. 检查数据是否有效
            if not self._validate_data_values(df):
                return False, f"{period}周期数据包含无效值"
            
            # 6. 检查时间序列的连续性
            if not self._validate_time_continuity(df, period):
                return False, f"{period}周期数据时间序列不连续"
            
            return True, None
            
        except Exception as e:
            self.logger.error(f"数据验证失败: {str(e)}")
            return False, f"数据验证过程出错: {str(e)}"

    def _validate_data_types(self, df: pd.DataFrame) -> bool:
        """
        验证数据类型
        """
        try:
            # 检查datetime列
            if not pd.api.types.is_datetime64_any_dtype(df['datetime']):
                self.logger.error("datetime列类型错误")
                return False
            
            # 检查数值列
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_cols:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    self.logger.error(f"{col}列类型错误")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"数据类型验证失败: {str(e)}")
            return False

    def _validate_data_values(self, df: pd.DataFrame) -> bool:
        """
        验证数据值的有效性
        """
        try:
            # 检查是否有空值
            if df[self.required_columns].isnull().any().any():
                self.logger.error("数据包含空值")
                return False
            
            # 检查价格是否为正数
            price_cols = ['open', 'high', 'low', 'close']
            if (df[price_cols] <= 0).any().any():
                self.logger.error("价格数据包含非正数")
                return False
            
            # 检查成交量是否为非负数
            if (df['volume'] < 0).any():
                self.logger.error("成交量包含负数")
                return False
            
            # 检查OHLC逻辑关系
            invalid_ohlc = (
                (df['high'] < df['low']) |
                (df['high'] < df['open']) |
                (df['high'] < df['close']) |
                (df['low'] > df['open']) |
                (df['low'] > df['close'])
            )
            if invalid_ohlc.any():
                self.logger.error("OHLC数据逻辑关系错误")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"数据值验证失败: {str(e)}")
            return False

    def _validate_time_continuity(self, 
                                df: pd.DataFrame, 
                                period: str) -> bool:
        """
        验证时间序列的连续性
        """
        try:
            # 获取时间间隔
            time_delta = self._get_time_delta(period)
            if time_delta is None:
                return False
            
            # 检查时间序列是否按升序排列
            if not df['datetime'].is_monotonic_increasing:
                self.logger.error("时间序列未按升序排列")
                return False
            
            # 计算时间差
            time_diffs = df['datetime'].diff()[1:]
            expected_diff = pd.Timedelta(time_delta)
            
            # 允许的误差范围（1分钟）
            tolerance = pd.Timedelta('1 minute')
            
            # 检查时间间隔是否符合预期
            invalid_diffs = abs(time_diffs - expected_diff) > tolerance
            if invalid_diffs.any():
                self.logger.error("时间序列不连续")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"时间连续性验证失败: {str(e)}")
            return False

    def _get_time_delta(self, period: str) -> Optional[str]:
        """
        根据周期获取时间间隔
        """
        period_map = {
            '15m': '15 minutes',
            '30m': '30 minutes',
            '1h': '1 hour',
            '2h': '2 hours',
            '4h': '4 hours',
            '1d': '1 day'
        }
        
        if period not in period_map:
            self.logger.error(f"不支持的周期: {period}")
            return None
            
        return period_map[period]

    def validate_all_periods(self, 
                           period_data: Dict[str, pd.DataFrame]) -> List[str]:
        """
        验证所有周期的数据
        
        Args:
            period_data: 不同周期的数据字典
            
        Returns:
            List[str]: 错误信息列表
        """
        errors = []
        
        for period, df in period_data.items():
            is_valid, error_msg = self.validate_data(df, period)
            if not is_valid:
                errors.append(f"{period}周期: {error_msg}")
        
        return errors

    def validate_kline_data(self, df: pd.DataFrame) -> bool:
        """验证K线数据的完整性和有效性"""
        try:
            # 检查必要列是否存在
            required_columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_columns):
                self.logger.error(f"缺少必要列：{[col for col in required_columns if col not in df.columns]}")
                return False
                
            # 检查数据类型
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    self.logger.error(f"{col}列不是数值类型")
                    return False
                    
            # 检查是否有无效值
            if df[numeric_columns].isnull().any().any():
                self.logger.warning("数据中存在空值")
                return False
                
            # 检查价格逻辑
            invalid_price = (
                (df['low'] > df['high']) |
                (df['open'] > df['high']) |
                (df['open'] < df['low']) |
                (df['close'] > df['high']) |
                (df['close'] < df['low'])
            ).any()
            
            if invalid_price:
                self.logger.error("价格数据存在逻辑错误")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"数据验证失败: {str(e)}")
            return False
            
    def validate_capital_flow(self, df: pd.DataFrame) -> bool:
        """验证资金流向数据的有效性"""
        try:
            # 检查必要列
            required_columns = ['datetime', 'capital_inflow', 'capital_outflow', 'capital_netflow']
            if not all(col in df.columns for col in required_columns):
                self.logger.error(f"缺少必要列：{[col for col in required_columns if col not in df.columns]}")
                return False
                
            # 检查数据类型
            numeric_columns = ['capital_inflow', 'capital_outflow', 'capital_netflow']
            for col in numeric_columns:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    self.logger.error(f"{col}列不是数值类型")
                    return False
                    
            # 验证资金净流入计算是否正确
            calculated_netflow = df['capital_inflow'] - df['capital_outflow']
            if not np.allclose(calculated_netflow, df['capital_netflow'], rtol=1e-5):
                self.logger.error("资金净流入计算有误")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"资金流向数据验证失败: {str(e)}")
            return False
            
    def validate_indicators(self, df: pd.DataFrame) -> bool:
        """
        验证技术指标的有效性
        
        Args:
            df: 包含技术指标的DataFrame
            
        Returns:
            bool: 是否通过验证
        """
        try:
            # 检查MA指标
            ma_cols = [col for col in df.columns if col.startswith('ma')]
            for col in ma_cols:
                if not self._validate_ma(df[col]):
                    return False
            
            # 检查MACD指标
            macd_cols = ['macd_dif', 'macd_dea', 'macd_hist']
            if all(col in df.columns for col in macd_cols):
                if not self._validate_macd(df[macd_cols]):
                    return False
            
            # 检查KDJ指标
            kdj_cols = ['kdj_k', 'kdj_d', 'kdj_j']
            if all(col in df.columns for col in kdj_cols):
                if not self._validate_kdj(df[kdj_cols]):
                    return False
            
            # 检查RSI指标
            rsi_cols = [col for col in df.columns if col.startswith('rsi')]
            for col in rsi_cols:
                if not self._validate_rsi(df[col]):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"技术指标验证失败: {str(e)}")
            return False

    def _validate_ma(self, series: pd.Series) -> bool:
        """验证MA指标的有效性"""
        try:
            # MA应该在最高价和最低价之间
            if series.isnull().all():
                self.logger.error("MA数据全部为空")
                return False
            
            # MA应该是平滑的，检查突变
            diff = series.diff().abs()
            if (diff > series.mean() * 0.5).any():
                self.logger.warning("MA数据存在异常突变")
            
            return True
            
        except Exception as e:
            self.logger.error(f"MA指标验证失败: {str(e)}")
            return False

    def _validate_macd(self, df: pd.DataFrame) -> bool:
        """验证MACD指标的有效性"""
        try:
            dif, dea, hist = df['macd_dif'], df['macd_dea'], df['macd_hist']
            
            # 验证HIST是否等于2*(DIF-DEA)
            calc_hist = 2 * (dif - dea)
            if not np.allclose(hist, calc_hist, rtol=1e-3):
                self.logger.error("MACD HIST计算错误")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"MACD指标验证失败: {str(e)}")
            return False

    def _validate_kdj(self, df: pd.DataFrame) -> bool:
        """验证KDJ指标的有效性"""
        try:
            k, d, j = df['kdj_k'], df['kdj_d'], df['kdj_j']
            
            # K、D值应该在0-100之间
            if ((k < 0) | (k > 100) | (d < 0) | (d > 100)).any():
                self.logger.error("KDJ的K或D值超出范围[0,100]")
                return False
            
            # J值通常在-100到100之间，但可能超出
            if ((j < -100) | (j > 100)).any():
                self.logger.warning("KDJ的J值超出正常范围[-100,100]")
            
            # 验证J = 3K - 2D
            calc_j = 3 * k - 2 * d
            if not np.allclose(j, calc_j, rtol=1e-3):
                self.logger.error("KDJ的J值计算错误")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"KDJ指标验证失败: {str(e)}")
            return False

    def _validate_rsi(self, series: pd.Series) -> bool:
        """验证RSI指标的有效性"""
        try:
            # RSI应该在0-100之间
            if ((series < 0) | (series > 100)).any():
                self.logger.error("RSI值超出范围[0,100]")
                return False
            
            # 检查RSI的连续性
            diff = series.diff().abs()
            if (diff > 30).any():  # RSI通常不会出现太大的跳变
                self.logger.warning("RSI数据存在异常突变")
            
            return True
            
        except Exception as e:
            self.logger.error(f"RSI指标验证失败: {str(e)}")
            return False

    def validate_and_fix_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """
        验证并修复数据
        
        Args:
            df: 待验证的DataFrame
            
        Returns:
            Tuple[pd.DataFrame, List[str]]: (修复后的DataFrame, 警告信息列表)
        """
        warnings = []
        
        # 1. 处理重复的时间戳
        if df['datetime'].duplicated().any():
            df = df.drop_duplicates(subset=['datetime'], keep='first')
            warnings.append("发现并删除重复的时间戳")
        
        # 2. 处理空值
        if df[self.required_columns].isnull().any().any():
            # 对于价格，使用前值填充
            price_cols = ['open', 'high', 'low', 'close']
            df[price_cols] = df[price_cols].fillna(method='ffill')
            
            # 对于成交量，使用0填充
            df['volume'] = df['volume'].fillna(0)
            
            warnings.append("发现并填充了空值")
        
        # 3. 修正异常价格
        price_cols = ['open', 'high', 'low', 'close']
        for col in price_cols:
            mask = (df[col] < self.price_limits['min']) | (df[col] > self.price_limits['max'])
            if mask.any():
                df.loc[mask, col] = df[col].rolling(window=3, min_periods=1).mean()
                warnings.append(f"修正了{col}列的异常价格")
        
        # 4. 修正OHLC关系
        df = self._fix_ohlc_relationship(df)
        
        # 5. 按时间排序
        df = df.sort_values('datetime')
        
        return df, warnings

    def _fix_ohlc_relationship(self, df: pd.DataFrame) -> pd.DataFrame:
        """修正OHLC价格之间的关系"""
        # 确保high >= low
        df['high'] = df[['high', 'low']].max(axis=1)
        df['low'] = df[['high', 'low']].min(axis=1)
        
        # 确保high >= open, close
        df['high'] = df[['high', 'open', 'close']].max(axis=1)
        
        # 确保low <= open, close
        df['low'] = df[['low', 'open', 'close']].min(axis=1)
        
        return df

def validate_and_fix_columns(df: pd.DataFrame, 
                           standard_columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    验证并修复DataFrame的列，确保所有必要的列都存在且顺序正确。
    
    Args:
        df: 输入的DataFrame
        standard_columns: 标准列名列表，如果为None则使用默认列表
        
    Returns:
        修复后的DataFrame
    """
    if standard_columns is None:
        standard_columns = [
            'datetime', 'open', 'high', 'low', 'close', 'volume',
            'macd', 'signal', 'hist',
            'k', 'd', 'j',
            'rsi_6', 'rsi_12', 'rsi_24'
        ]
    
    try:
        # 将列名转换为小写
        df.columns = df.columns.str.lower()
        
        # 创建一个新的DataFrame，包含现有列并用默认值填充缺失列
        new_df = pd.DataFrame()
        
        # 处理datetime列
        if 'datetime' in df.columns:
            new_df['datetime'] = pd.to_datetime(df['datetime'])
        else:
            logger.warning("Missing datetime column")
            return None
            
        # 处理必要的价格和成交量列
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                new_df[col] = pd.to_numeric(df[col], errors='coerce')
            else:
                logger.warning(f"Missing {col} column")
                new_df[col] = 0.0
                
        # 处理技术指标列
        for col in standard_columns[6:]:  # 跳过基本列
            if col in df.columns:
                new_df[col] = pd.to_numeric(df[col], errors='coerce')
            else:
                new_df[col] = np.nan
                
        # 确保列的顺序与standard_columns一致
        new_df = new_df[standard_columns]
        
        return new_df
        
    except Exception as e:
        logger.error(f"Error in validate_and_fix_columns: {str(e)}")
        return None 