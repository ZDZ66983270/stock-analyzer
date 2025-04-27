import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib.dates as mdates
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def download_with_retry(ticker, start_date, end_date, max_retries=3):
    """带重试机制的数据下载函数"""
    for attempt in range(max_retries):
        try:
            data = yf.download(ticker, start=start_date, end=end_date, timeout=30)
            if not data.empty and 'Close' in data.columns:
                values = data['Close'].values.flatten()
                series = pd.Series(values, index=data.index)
                series.index = pd.to_datetime(series.index).tz_localize(None)
                return series
        except Exception as e:
            if attempt == max_retries - 1:
                raise Exception(f"下载{ticker}数据失败: {str(e)}")
            print(f"第{attempt + 1}次尝试下载失败，正在重试...")
    return None

def get_fed_rate(start_date, end_date):
    """获取联邦基准利率数据"""
    try:
        # 使用 ^IRX（13周国债收益率）作为联邦基准利率的近似
        fed_data = yf.download("^IRX", start=start_date, end=end_date, timeout=30)
        if not fed_data.empty and 'Close' in fed_data.columns:
            values = fed_data['Close'].values.flatten()
            series = pd.Series(values, index=fed_data.index)
            series.index = pd.to_datetime(series.index).tz_localize(None)
            return series
    except Exception as e:
        raise Exception(f"获取联邦基准利率数据失败: {str(e)}")
    return None

def get_aligned_data(series1, series2):
    """对齐两个时间序列数据"""
    if series1 is None or series2 is None:
        raise Exception("无法获取完整的数据")
    
    common_dates = series1.index.intersection(series2.index)
    if len(common_dates) == 0:
        raise Exception("没有找到匹配的数据日期")
    
    return series1[common_dates], series2[common_dates]

def get_treasury_ticker(duration):
    """根据久期返回对应的ticker"""
    if duration == 30:
        return "^TYX", "30年期国债收益率"
    elif duration == 20:
        return "^TYX", "20年期国债收益率（使用30年期数据近似）"
    elif duration == 10:
        return "^TNX", "10年期国债收益率"
    elif duration == 5:
        return "^FVX", "5年期国债收益率"
    elif duration == 2:
        return "^IRX", "2年期国债收益率"
    else:
        raise ValueError("不支持的国债久期")

def plot_yields_comparison():
    print("\n=== 国债收益率与联邦基准利率对比分析 ===\n")
    
    try:
        # 用户输入
        year = int(input("请输入起始年份 (例如: 2023): "))
        if year < 1990 or year > datetime.now().year:
            raise ValueError("请输入有效的年份（1990至今）")
            
        print("\n可选择的国债久期：")
        print("2  - 2年期国债")
        print("5  - 5年期国债")
        print("10 - 10年期国债")
        print("20 - 20年期国债")
        print("30 - 30年期国债")
        
        # 颜色列表 - 修改这里，确保有足够的颜色
        COLORS = {
            1: ['blue'],
            2: ['blue', 'purple']
        }
        
        # 获取用户选择的国债数量
        num_bonds = int(input("\n请选择要对比的国债数量 (1-2): "))
        if num_bonds not in [1, 2]:
            raise ValueError("只能选择1-2个国债进行对比")
            
        # 根据选择的数量获取对应的颜色列表
        colors = COLORS[num_bonds]
        
        # 存储选择的国债信息
        selected_bonds = []
        for i in range(num_bonds):
            duration = int(input(f"\n请输入第{i+1}个国债久期 (年): "))
            if duration not in [2, 5, 10, 20, 30]:
                raise ValueError("目前只支持2年期、5年期、10年期、20年期和30年期国债")
            selected_bonds.append(duration)
        
        # 设置时间范围
        start_date = f"{year}-01-01"
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        # 创建图表
        plt.figure(figsize=(12, 6))
        
        # 获取联邦基准利率数据
        print("\n正在下载联邦基准利率数据...")
        fed_rates = get_fed_rate(start_date, end_date)
        if fed_rates is None:
            raise Exception("无法获取联邦基准利率数据")
        
        # 存储所有数据用于计算利差
        all_data = {'联邦基准利率': fed_rates}
        
        # 下载并绘制每个选择的国债数据
        for i, duration in enumerate(selected_bonds):
            ticker, label = get_treasury_ticker(duration)
            print(f"\n正在下载{label}数据...")
            
            treasury_yields = download_with_retry(ticker, start_date, end_date)
            if treasury_yields is None:
                raise Exception(f"无法获取{label}数据")
            
            all_data[label] = treasury_yields
            
            # 绘制国债收益率曲线
            plt.plot(treasury_yields.index, treasury_yields.values,
                    label=label, color=colors[i])
            
            # 在曲线末端添加数值标注
            last_date = treasury_yields.index[-1]
            last_value = treasury_yields.iloc[-1]
            plt.annotate(f'{last_value:.2f}%',
                        xy=(last_date, last_value),
                        xytext=(10, 10),
                        textcoords='offset points',
                        ha='left',
                        va='bottom',
                        bbox=dict(boxstyle='round,pad=0.5', fc=colors[i], alpha=0.1),
                        color=colors[i])
        
        # 绘制联邦基准利率
        plt.plot(fed_rates.index, fed_rates.values,
                label='联邦基准利率', color='red')
        
        # 添加联邦基准利率标注
        last_fed = fed_rates.iloc[-1]
        plt.annotate(f'{last_fed:.2f}%',
                    xy=(fed_rates.index[-1], last_fed),
                    xytext=(10, -10),
                    textcoords='offset points',
                    ha='left',
                    va='top',
                    bbox=dict(boxstyle='round,pad=0.5', fc='red', alpha=0.1),
                    color='red')
        
        # 计算并绘制利差
        for i, (label, data) in enumerate(all_data.items()):
            if label != '联邦基准利率':
                spread = data - fed_rates
                plt.plot(spread.index, spread.values,
                        label=f'{label}利差',
                        color=colors[i],
                        linestyle='--')
                
                # 添加利差标注
                last_spread = spread.iloc[-1]
                plt.annotate(f'{last_spread:.2f}%',
                            xy=(spread.index[-1], last_spread),
                            xytext=(10, 0),
                            textcoords='offset points',
                            ha='left',
                            va='center',
                            bbox=dict(boxstyle='round,pad=0.5', fc=colors[i], alpha=0.1),
                            color=colors[i])
        
        # 设置图表格式
        plt.title(f'国债收益率与联邦基准利率对比 ({year}年至今)')
        plt.xlabel('日期')
        plt.ylabel('利率 (%)')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        
        # 设置x轴日期格式
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        plt.xticks(rotation=45)
        
        # 打印当前数据
        print("\n=== 当前数据 ===")
        print(f"联邦基准利率: {last_fed:.2f}%")
        for label, data in all_data.items():
            if label != '联邦基准利率':
                last_value = data.iloc[-1]
                spread = last_value - last_fed
                print(f"{label}: {last_value:.2f}%")
                print(f"{label}利差: \033[33m{spread:.2f}%\033[0m")
        
        plt.tight_layout()
        plt.show()
        
    except ValueError as e:
        print(f"\n错误：{str(e)}")
    except Exception as e:
        print(f"\n错误：{str(e)}")
        print("请检查网络连接或稍后重试")

if __name__ == "__main__":
    while True:
        plot_yields_comparison()
        
        choice = input("\n是否继续分析？(Y/N): ").upper()
        if choice != 'Y':
            break
    
    print("\n感谢使用国债收益率分析工具！") 