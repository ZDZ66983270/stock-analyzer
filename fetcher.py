import os
import pytz

class DataFetcher:
    def __init__(self):
        # 美股市场代码前缀
        self.us_market_prefix = {
            # NASDAQ上市公司用105
            'MSFT': '105', 'AAPL': '105', 'GOOGL': '105', 'AMZN': '105', 'META': '105',
            # NYSE上市ADR用106
            'TSM': '106'
        }
        # 设置时区
        self.est_tz = pytz.timezone('US/Eastern')
        # 读取股票列表
        self.symbols = self._load_symbols()
        
    def _load_symbols(self) -> list:
        """从根目录下的 symbols.txt 加载股票列表"""
        symbols = []
        try:
            # 使用绝对路径确保读取根目录下的文件
            script_dir = os.path.dirname(os.path.abspath(__file__))
            symbols_file = os.path.join(os.path.dirname(script_dir), 'symbols.txt')
            
            with open(symbols_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # 跳过空行和注释行
                    if line and not line.startswith('#'):
                        symbols.append(line)
            print(f"Loaded symbols: {symbols}")
        except Exception as e:
            print(f"Error loading symbols: {str(e)}")
        return symbols 