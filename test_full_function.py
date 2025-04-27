from stock_analyzer import StockAnalyzer
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_full_function():
    """测试完整功能"""
    analyzer = StockAnalyzer()
    symbols = ['SH.600536', 'HK.09988', 'US.TSM']
    
    for symbol in symbols:
        print(f"\n开始处理股票 {symbol}:")
        try:
            results = analyzer.process_stock_data(symbol)
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
            print(f"处理 {symbol} 时发生错误: {str(e)}")
            continue

if __name__ == '__main__':
    test_full_function() 