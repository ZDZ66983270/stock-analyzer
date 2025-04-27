import sys
import subprocess
import os
from datetime import datetime, timedelta
import pytz
from typing import List, Optional, Tuple, Dict
import logging
import pandas as pd
import requests

from get_indicator import get_all_indicators
from fetch_kline_data import fetch_stock_data
from fetch_capital_flow import fetch_capital_flow
from fetch_chip_distribution import fetch_chip_distribution
from merge_data import merge_all_data, save_merged_data
from config import validate_stock_list

def get_local_date():
    """获取本地日期"""
    local_tz = pytz.timezone('Asia/Shanghai')  # 使用上海时区
    local_now = datetime.now()
    local_now = local_tz.localize(local_now)
    return local_now.replace(hour=0, minute=0, second=0, microsecond=0)

def main_menu():
    while True:
        print("\n请选择一个操作：")
        print("1. 股票新高后回落分析，运行本地的 stock_highdrop.py")
        print("2. 最优方案对比，运行本地的 Best_Solution.py")
        print("3. 股票对比，运行本地的 stock_index.py")
        print("4. 大选年指数分析，运行本地的 election_year.py")
        print("5. 获取分红和股息率，运行本地的 dividend_yield.py")
        print("6. 获取换手率，运行本地的 turnover_ratio.py")
        print("7. 12个月股价排序，运行本地的 month_comparison.py")
        print("8. 对比A股港股价差，运行本地的 CN & HK comparison.py")
        print("9. 股票 vs 期权分析，运行本地的 stock_options.py")
        print("10. 国债目标收益率计算，运行本地的 bond_yield.py")
        print("11. 国债收益率曲线分析，运行本地的 bond_comparison.py")
        print("12. 股票数据分析（K线+指标+资金流+筹码）")
        print("13. 技术指标分析")
        print("14. 批量处理")
        print("0. 退出，本程序关闭")

        choice = input("请输入选项（0-14）：")

        if choice == '1':
            print("正在运行股票新高后回落分析...")
            subprocess.run([sys.executable, "stock_highdrop.py"])
        elif choice == '2':
            print("正在运行最优方案对比...")
            subprocess.run([sys.executable, "Best_Solution.py"])
        elif choice == '3':
            print("正在运行股票对比...")
            subprocess.run([sys.executable, "stock_index.py"])
        elif choice == '4':
            print("正在运行大选年指数分析...")
            subprocess.run([sys.executable, "election_year.py"])
        elif choice == '5':
            print("正在运行分红和股息率分析...")
            subprocess.run([sys.executable, "dividend_yield.py"])
        elif choice == '6':
            print("正在运行换手率分析...")
            subprocess.run([sys.executable, "turnover_ratio.py"])
        elif choice == '7':
            print("正在运行12个月股价排序分析...")
            subprocess.run([sys.executable, "month_comparison.py"])
        elif choice == '8':
            print("正在对比A股港股价差...")
            subprocess.run([sys.executable, "CN & HK comparison.py"])
        elif choice == '9':
            print("正在运行股票 vs 期权分析...")
            subprocess.run([sys.executable, "stock_options.py"])
        elif choice == '10':
            print("=== 运行国债目标收益率计算器（bond_yield.py） ===")
            try:
                subprocess.run([sys.executable, "bond_yield.py"], check=True)
            except subprocess.CalledProcessError as e:
                print(f"运行 bond_yield.py 时出错: {e}")
            except FileNotFoundError:
                print("未找到 bond_yield.py 文件，请确认文件路径是否正确")
            input("\n按回车键继续...")
        elif choice == '11':
            print("=== 运行国债收益率曲线分析（bond_comparison.py） ===")
            try:
                subprocess.run([sys.executable, "bond_comparison.py"], check=True)
            except subprocess.CalledProcessError as e:
                print(f"运行 bond_comparison.py 时出错: {e}")
            except FileNotFoundError:
                print("未找到 bond_comparison.py 文件，请确认文件路径是否正确")
            input("\n按回车键继续...")
        elif choice == '12':
            print("正在运行股票数据分析（K线+指标+资金流+筹码）...")
            Menu().run()
        elif choice == '13':
            print("正在运行技术指标分析...")
            Menu().technical_indicators()
        elif choice == '14':
            print("正在运行批量处理...")
            Menu().batch_process()
        elif choice == '0':
            print("程序结束。")
            break
        else:
            print("无效输入，请重新选择。")

def calculate_bond_yield():
    print("\n=== 国债目标收益率计算器 ===\n")
    
    try:
        face_value = float(input("请输入国债面值（元）: "))
        market_price = float(input("请输入市场价格（元）: "))
        coupon_rate = float(input("请输入票面利率（%）: ")) / 100
        years_to_maturity = float(input("请输入剩余年限（年）: "))
        
        # 计算年息票金额
        annual_coupon = face_value * coupon_rate
        
        # 简单收益率计算 = (年息票 + (面值-市价)/年限) / 市价
        simple_yield = (annual_coupon + (face_value - market_price) / years_to_maturity) / market_price * 100
        
        print("\n=== 计算结果 ===")
        print(f"简单收益率: {simple_yield:.2f}%")
        
    except ValueError:
        print("\n错误：请输入有效的数字！")
    except ZeroDivisionError:
        print("\n错误：市场价格不能为零！")
    except Exception as e:
        print(f"\n发生错误: {str(e)}")

def validate_stock_symbols(symbols: List[str]) -> Tuple[bool, str]:
    """
    验证股票代码格式和数量
    返回: (是否有效, 错误信息)
    """
    if len(symbols) > 9:
        return False, "股票数量超过限制（最多9只）"
    
    valid_prefixes = {'US.', 'HK.', 'SH.', 'SZ.'}
    for symbol in symbols:
        parts = symbol.split('.')
        if len(parts) != 2 or parts[0] not in valid_prefixes:
            return False, f"股票代码 {symbol} 格式错误（应为 US.MSFT 格式）"
    
    return True, ""

def fetch_minute_kline(symbol: str, period: str) -> pd.DataFrame:
    """
    获取分钟级K线数据
    period: 周期（4h、2h、1h、30m、15m、5m、3m）
    """
    try:
        if symbol.startswith('US.'):
            # 使用雅虎金融API获取美股分钟数据
            params = {
                'includePrePost': 'true',  # 包含盘前盘后数据
            }
        elif symbol.startswith('HK.'):
            # 使用富途API获取港股分钟数据
            pass
        else:
            # 使用东方财富API获取A股分钟数据
            pass
    except Exception as e:
        logging.error(f"获取分钟数据失败: {symbol} {period} - {str(e)}")
        return None

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """计算所有技术指标"""
    # MA系列
    for period in [5, 10, 20]:
        df[f'MA{period}'] = df['Close'].rolling(period).mean()
    
    # MACD
    df = calculate_macd(df)
    
    # KDJ
    df = calculate_kdj(df)
    
    # RSI
    for period in [6, 12, 24]:
        df[f'RSI{period}'] = calculate_rsi(df['Close'], period)
    
    return df

def fetch_xueqiu_data(symbol: str) -> Dict:
    """获取雪球网资金流数据"""
    headers = {
        'User-Agent': '...',
        'Cookie': '...'  # 需要登录态
    }
    
    try:
        response = requests.get(f'https://stock.xueqiu.com/v5/stock/capital/flow/{symbol}.json',
                              headers=headers)
        data = response.json()
        if 'Amount' not in data['data']:
            data['data']['Amount'] = data['data']['Volume'] * (data['data']['High'] + data['data']['Low']) / 2
        return {
            'inflow': data['data']['inflow'],
            'outflow': data['data']['outflow'],
            'net_inflow': data['data']['net_inflow']
        }
    except Exception as e:
        logging.error(f"获取雪球数据失败: {symbol} - {str(e)}")
        return None

def merge_and_save_data(symbol: str, 
                       kline_data: Dict[str, pd.DataFrame],
                       indicators: pd.DataFrame,
                       flow_data: Dict) -> None:
    """合并所有数据并保存"""
    # 创建输出目录
    output_dir = f"output/{symbol}"
    os.makedirs(output_dir, exist_ok=True)
    
    # 合并数据
    merged_data = pd.DataFrame()
    for period, df in kline_data.items():
        # 添加周期数据
        for col in df.columns:
            merged_data[f"{period}_{col}"] = df[col]
    
    # 添加技术指标
    for col in indicators.columns:
        if col not in merged_data.columns:
            merged_data[col] = indicators[col]
    
    # 添加资金流数据
    for key, value in flow_data.items():
        merged_data[f"flow_{key}"] = value
    
    # 保存到CSV
    merged_data.to_csv(f"{output_dir}/{symbol}_data.csv", index=False)

class Menu:
    """菜单类"""
    
    def __init__(self):
        self.choices = {
            "1": self.stock_analysis,
            "2": self.technical_indicators,
            "3": self.batch_process,
            "4": self.quit
        }
    
    def display_menu(self):
        """显示菜单选项"""
        print("""
\n股票数据分析系统
1. 股票数据分析（K线+指标+资金流+筹码）
2. 技术指标分析
3. 批量处理
4. 退出
""")
    
    def run(self):
        """运行菜单"""
        while True:
            self.display_menu()
            choice = input("请输入您的选择: ")
            action = self.choices.get(choice)
            if action:
                action()
            else:
                print("{0} 不是有效选择".format(choice))
    
    def stock_analysis(self):
        """股票数据分析功能"""
        print("\n=== 股票数据分析 ===")
        print("请输入股票代码（最多9个，用空格分隔）")
        print("示例: AAPL GOOGL MSFT")
        
        # 获取股票代码
        stock_input = input("股票代码: ").strip()
        if not stock_input:
            print("错误：未输入股票代码")
            return
        
        stock_list = stock_input.split()
        
        # 验证股票列表
        if not validate_stock_list(stock_list):
            return
        
        # 获取日期范围
        end_date = get_local_date()
        days = input("请输入要获取的天数（默认30天）: ").strip()
        try:
            days = int(days) if days else 30
            start_date = end_date - timedelta(days=days)
        except ValueError:
            print("错误：无效的天数")
            return
        
        # 格式化日期为字符串
        end_date_str = end_date.strftime("%Y-%m-%d")
        start_date_str = start_date.strftime("%Y-%m-%d")
        
        print(f"\n开始处理 {len(stock_list)} 只股票的数据...")
        print(f"数据时间范围：{start_date_str} 至 {end_date_str}")
        
        # 处理每只股票
        for symbol in stock_list:
            try:
                print(f"\n开始处理股票 {symbol} 的数据...")
                
                # 1. 获取K线数据
                print("正在获取K线数据...")
                kline_data = fetch_stock_data(symbol, start_date_str, end_date_str)
                if not kline_data:
                    print(f"无法获取股票 {symbol} 的K线数据，跳过处理")
                    continue
                
                # 2. 获取资金流向数据
                print("正在获取资金流向数据...")
                capital_flow = fetch_capital_flow(symbol, start_date_str, end_date_str)
                
                # 3. 获取筹码分布数据
                print("正在计算筹码分布数据...")
                if '1d' in kline_data:
                    chip_distribution = fetch_chip_distribution(symbol, kline_data['1d'])
                else:
                    print("警告：没有日线数据，无法计算筹码分布")
                    chip_distribution = None
                
                # 4. 合并所有数据
                print("正在合并数据...")
                merged_data = merge_all_data(
                    symbol,
                    kline_data,
                    capital_flow,
                    chip_distribution
                )
                
                # 5. 保存数据
                save_merged_data(symbol, merged_data)
                print(f"股票 {symbol} 的数据处理完成")
                
            except Exception as e:
                print(f"处理股票 {symbol} 时发生错误: {str(e)}")
        
        print("\n所有股票处理完成！")
    
    def technical_indicators(self):
        """技术指标分析功能"""
        print("\n=== 技术指标分析 ===")
        symbol = input("请输入股票代码: ").strip()
        if not symbol:
            print("错误：未输入股票代码")
            return
        
        start_date = input("请输入开始日期 (YYYY-MM-DD): ").strip()
        end_date = input("请输入结束日期 (YYYY-MM-DD): ").strip()
        
        try:
            indicators = get_all_indicators(symbol, start_date, end_date)
            if indicators:
                print("\n获取到以下技术指标数据：")
                for indicator_name in indicators.keys():
                    print(f"- {indicator_name}")
            else:
                print("获取技术指标数据失败")
        except Exception as e:
            print(f"处理出错: {str(e)}")
    
    def batch_process(self):
        """批量处理功能"""
        print("\n=== 批量处理 ===")
        print("该功能正在开发中...")
    
    def quit(self):
        """退出程序"""
        print("\n感谢使用！再见！")
        sys.exit(0)

if __name__ == "__main__":
    main_menu()
