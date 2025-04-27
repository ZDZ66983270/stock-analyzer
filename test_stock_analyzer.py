import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from stock_analyzer import StockAnalyzer
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class TestStockAnalyzer(unittest.TestCase):
    def setUp(self):
        """测试前的准备工作"""
        self.analyzer = StockAnalyzer()
        
        # 创建测试数据
        dates = pd.date_range(start='2024-01-01', end='2024-01-10', freq='D')
        self.test_data = pd.DataFrame({
            'datetime': dates,
            'open': np.random.uniform(10, 20, len(dates)),
            'high': np.random.uniform(15, 25, len(dates)),
            'low': np.random.uniform(5, 15, len(dates)),
            'close': np.random.uniform(10, 20, len(dates)),
            'volume': np.random.uniform(1000, 10000, len(dates))
        })
        
        # 修正OHLC关系
        self.test_data['high'] = self.test_data[['open', 'high', 'close']].max(axis=1)
        self.test_data['low'] = self.test_data[['open', 'low', 'close']].min(axis=1)
        
        # 创建测试用的多周期数据
        self.period_data = {
            '1d': self.test_data.copy(),
            '1h': self.test_data.copy(),
            '30m': self.test_data.copy(),
            '15m': self.test_data.copy()
        }

    def test_fetch_stock_data(self):
        """测试股票数据获取功能"""
        # 测试无效的股票代码格式
        with self.assertRaises(ValueError):
            self.analyzer.fetch_stock_data('AAPL')  # 缺少市场代码
        
        # 测试不支持的市场
        with self.assertRaises(ValueError):
            self.analyzer.fetch_stock_data('XX.AAPL')
        
        # 测试A股数据获取
        cn_data = self.analyzer.fetch_stock_data('SH.600000')
        if cn_data:  # 如果能获取到数据
            self.assertIsInstance(cn_data, dict)
            for period, df in cn_data.items():
                self.assertFalse(df.empty)
                self.assertTrue('datetime' in df.columns)
                self.assertTrue('close' in df.columns)

    def test_calculate_indicators(self):
        """测试技术指标计算功能"""
        # 计算技术指标
        results = self.analyzer.calculate_indicators(self.period_data)
        
        # 验证结果
        self.assertIsInstance(results, dict)
        for period, indicators in results.items():
            # 检查是否包含所有必要的指标
            self.assertIn('macd', indicators)
            self.assertIn('kdj', indicators)
            self.assertIn('rsi', indicators)

    def test_calculate_macd(self):
        """测试MACD计算"""
        df = self.test_data.copy()
        result = self.analyzer.calculate_macd(df)
        
        # 验证MACD计算结果
        self.assertIn('MACD_1d', result.columns)
        self.assertIn('MACD_1d_Signal', result.columns)
        self.assertIn('MACD_1d_Hist', result.columns)

    def test_calculate_kdj(self):
        """测试KDJ计算"""
        df = self.test_data.copy()
        result = self.analyzer.calculate_kdj(df)
        
        # 验证KDJ计算结果
        self.assertIn('KDJ_1d_K', result.columns)
        self.assertIn('KDJ_1d_D', result.columns)
        self.assertIn('KDJ_1d_J', result.columns)
        
        # 验证K、D值是否在0-100范围内
        self.assertTrue((result['KDJ_1d_K'] >= 0).all() and (result['KDJ_1d_K'] <= 100).all())
        self.assertTrue((result['KDJ_1d_D'] >= 0).all() and (result['KDJ_1d_D'] <= 100).all())

    def test_calculate_rsi(self):
        """测试RSI计算"""
        df = self.test_data.copy()
        
        # 添加一些极端情况的数据
        df.loc[5:8, 'close'] = df.loc[4, 'close']  # 连续相同价格
        df.loc[9, 'close'] = df.loc[8, 'close'] * 2  # 大幅上涨
        
        result = self.analyzer.calculate_rsi(df)
        
        # 验证RSI计算结果
        for period in [6, 12, 24]:
            column = f'RSI_1d_{period}'
            self.assertIn(column, result.columns)
            
            # 验证RSI值是否在0-100范围内
            self.assertTrue((result[column] >= 0).all() and (result[column] <= 100).all(),
                          f"{column}的值超出范围[0,100]")
            
            # 验证RSI的计算结果是否合理
            rsi_values = result[column].dropna()
            self.assertTrue(len(rsi_values) > 0, f"{column}的所有值都是NaN")
            
            # 验证极端情况的处理
            # 连续相同价格应该产生接近50的RSI值
            self.assertAlmostEqual(result.loc[8, column], 50.0, delta=10,
                                 msg=f"{column}在价格不变时应接近50")
            
            # 大幅上涨应该产生较高的RSI值
            self.assertTrue(result.loc[9, column] > 70,
                          f"{column}在价格大幅上涨时应该大于70")

    def test_calculate_ma(self):
        """测试MA计算"""
        df = self.test_data.copy()
        result = self.analyzer.calculate_ma(df, '1d')
        
        # 验证MA计算结果
        for period in [5, 10, 20]:
            column = f'ma{period}_1d'
            self.assertIn(column, result.columns)

    def test_save_to_excel(self):
        """测试数据保存到Excel的功能"""
        # 确保输出目录存在
        if not os.path.exists(self.analyzer.output_dir):
            os.makedirs(self.analyzer.output_dir)
        
        # 测试保存功能
        symbol = 'TEST.STOCK'
        self.analyzer.save_to_excel(symbol, self.period_data)
        
        # 验证文件是否创建
        expected_file = os.path.join(self.analyzer.output_dir, f"{symbol.replace('.', '_')}_data.xlsx")
        self.assertTrue(os.path.exists(expected_file))
        
        # 清理测试文件
        os.remove(expected_file)

    def test_error_handling(self):
        """测试错误处理"""
        # 测试无效的股票代码格式
        with self.assertRaises(ValueError):
            self.analyzer.fetch_stock_data('INVALID')
        
        # 测试不支持的市场
        with self.assertRaises(ValueError):
            self.analyzer.fetch_stock_data('XX.AAPL')
        
        # 测试空数据处理
        empty_data = pd.DataFrame()
        results = self.analyzer.calculate_indicators({'1d': empty_data})
        self.assertEqual(results, {})

    def test_real_time_data(self):
        """测试实时数据获取"""
        # 测试获取实时数据
        symbol = 'SH.600000'  # 浦发银行
        latest_data = self.analyzer.fetch_stock_data(symbol)
        
        # 验证返回的数据
        self.assertIsNotNone(latest_data)
        if latest_data:
            for period, df in latest_data.items():
                self.assertFalse(df.empty)
                self.assertTrue('datetime' in df.columns)
                self.assertTrue('close' in df.columns)

    def test_multiple_periods(self):
        """测试多周期数据处理"""
        # 测试不同周期的数据计算
        for period in ['1d', '1h', '30m', '15m']:
            df = self.period_data[period]
            
            # 计算各项指标
            macd_result = self.analyzer.calculate_macd(df, period)
            kdj_result = self.analyzer.calculate_kdj(df, period)
            rsi_result = self.analyzer.calculate_rsi(df, period)
            ma_result = self.analyzer.calculate_ma(df, period)
            
            # 验证结果
            self.assertIsNotNone(macd_result)
            self.assertIsNotNone(kdj_result)
            self.assertIsNotNone(rsi_result)
            self.assertIsNotNone(ma_result)

def test_stock_analyzer():
    """
    测试股票分析器的主要功能
    """
    try:
        # 创建分析器实例
        analyzer = StockAnalyzer()
        
        # 测试用的股票代码（分别测试A股、港股和美股）
        test_symbols = [
            'SH.600000',  # 浦发银行
            'HK.00700',   # 腾讯控股
            'US.AAPL'     # 苹果公司
        ]
        
        # 测试每个股票
        for symbol in test_symbols:
            print(f"\n开始测试股票 {symbol} 的数据获取和分析...")
            
            # 调用完整的数据处理流程
            results = analyzer.process_stock_data(symbol)
            
            # 验证结果
            if results:
                print(f"✓ {symbol} 数据处理成功")
                # 检查各个周期的数据
                for period, df in results.items():
                    if period != 'fund_flow':
                        print(f"  - {period}周期: {len(df)}条记录")
                        # 验证技术指标是否存在
                        indicators = [
                            f'MACD_{period}',
                            f'KDJ_{period}_K',
                            f'RSI_{period}_6'
                        ]
                        for indicator in indicators:
                            if indicator in df.columns:
                                print(f"    ✓ {indicator}")
                            else:
                                print(f"    × {indicator} 缺失")
                    else:
                        print(f"  - 资金流数据: {len(df)}条记录")
            else:
                print(f"× {symbol} 数据处理失败")
            
            print("-" * 50)
            
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")

def run_tests():
    """运行所有测试"""
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStockAnalyzer)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试结果统计
    print("\n测试结果统计:")
    print(f"运行测试用例数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    test_stock_analyzer() 