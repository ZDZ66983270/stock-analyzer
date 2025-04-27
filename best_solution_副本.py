import yfinance as yf
import numpy as np
from datetime import datetime
import time

class StockAnalyzer:
    def __init__(self, stock, start_date, end_date):
        self.stock = stock
        self.start_date = start_date
        self.end_date = end_date
        self.data = None
        self.download_data()
        self.callback_percentages = []  # 用于记录每次新高后的回调百分比

    def download_data(self):
        """从Yahoo Finance下载股票数据，支持重试机制"""
        for attempt in range(3):  # 重试机制
            try:
                self.data = yf.download(self.stock, start=self.start_date, end=self.end_date, timeout=30)
                if self.data.empty:
                    raise ValueError(f"No data found for stock {self.stock}")
                self.data = self.data.dropna()  # 删除缺失值
                break
            except Exception as e:
                print(f"下载失败 (尝试 {attempt + 1}/3): {e}")
                time.sleep(5)  # 等待5秒再重试
        else:
            raise ValueError(f"无法下载股票数据: {self.stock}")

    def calculate_buy_and_hold(self, initial_investment, fee=20):
        """
        买入并持有策略：
        1. 第一天买入全部资金对应的股票。
        2. 最后一天按收盘价卖出所有股票。
        3. 计算并返回收益和交易记录，包含买入和卖出的手续费。
        """
        buy_price = float(self.data['Close'].iloc[0])  # 第一天收盘价
        sell_price = float(self.data['Close'].iloc[-1])  # 最后一天收盘价
        shares = initial_investment // buy_price
        remaining_cash = initial_investment - shares * buy_price - fee
        final_value = shares * sell_price + remaining_cash - fee
        profit = final_value - initial_investment
        trades = [
            {"action": "buy", "price": buy_price, "shares": shares, "amount": shares * buy_price, "fee": fee},
            {"action": "sell", "price": sell_price, "shares": shares, "amount": shares * sell_price, "fee": fee}
        ]
        return profit, final_value, trades

    def calculate_trading_strategy(self, initial_investment, fee=20, new_high_percentage=5):
        """
        高卖低买策略：
        - 按以下逻辑动态买入和卖出股票：
            1. **卖出逻辑**：
               - 当当前最高价相较于基准高点的涨幅 >= 用户设定的创新高百分比时，按当前最高价卖出。
               - 卖出价格为创新高的实际最高价。
               - 更新基准高点为当前最高价。
            2. **买入逻辑**：
               - 当当前最低价相较于基准高点的回调幅度 >= 历史回调中位数时，触发买入。
               - 买入价格为当天的最低价。
               - 买入价格必须低于最近一次卖出的价格，否则跳过。
            3. **强制清仓**：
               - 如果最后一天仍有股票未卖出，则按最后一天的收盘价强制清仓。
        """
        cash = initial_investment
        shares = 0
        base_high = -float('inf')  # 基准高点 (第一天用收盘价初始化)
        total_fees = 0
        trades = []

        print("开始分析交易数据...")
        for i in range(len(self.data)):
            price = float(self.data['Close'].iloc[i])  # 收盘价
            high = float(self.data['High'].iloc[i])  # 当日最高价
            low = float(self.data['Low'].iloc[i])  # 当日最低价
            date = self.data.index[i].strftime('%Y-%m-%d')

            # 第一日操作：用总资金买入，设置 base_high
            if i == 0:
                shares = cash // price
                cash -= shares * price + fee
                total_fees += fee
                base_high = price  # 将收盘价设为基准高点
                trades.append({
                    "action": "buy",
                    "price": price,
                    "shares": shares,
                    "amount": shares * price,
                    "cash_after": cash,
                    "fee": fee,
                    "date": date
                })
                print(f"第一天买入: 股价 ${price:.2f}, 数量 {shares:.2f}, 总金额 ${shares * price:.2f}, 现金余额 ${cash:.2f}")
                continue

            print(f"\n日期: {date}, 收盘价: ${price:.2f}, 最高价: ${high:.2f}, 最低价: ${low:.2f}, 当前基准高点: ${base_high:.2f}")

            # 卖出逻辑：检查是否创新高并超过指定百分比
            if high > base_high:
                high_increase_percentage = (high - base_high) / base_high * 100
                if high_increase_percentage >= new_high_percentage:  # 满足创新高幅度要求
                    if shares > 0:
                        sell_value = shares * high  # 按最高价卖出
                        cash += sell_value - fee
                        total_fees += fee
                        trades.append({
                            "action": "sell",
                            "price": high,
                            "shares": shares,
                            "amount": sell_value,
                            "cash_after": cash,
                            "fee": fee,
                            "date": date
                        })
                        print(f"卖出触发: 股价 ${high:.2f}, 数量 {shares:.2f}, 总金额 ${sell_value:.2f}, 现金余额 ${cash:.2f}")
                        shares = 0  # 清空持仓
                        self.callback_percentages.append((high - low) / high * 100)  # 记录回调百分比
                    base_high = high  # 更新基准高点
                else:
                    print(f"新高幅度百分比为 {high_increase_percentage:.2f}%，低于设定值，跳过卖出")

            # 动态计算回调中位数
            if self.callback_percentages:
                median_callback = np.median(self.callback_percentages)
            else:
                median_callback = 0  # 无回调记录时设为0

            # 买入逻辑：必须满足两个条件
            decline_percentage = (base_high - low) / base_high * 100
            if decline_percentage >= median_callback:  # 满足回调幅度条件
                if trades and trades[-1]['action'] == 'sell':  # 检查最近的卖出记录
                    last_sell_price = trades[-1]['price']
                    if low >= last_sell_price:  # 买入价必须低于最近卖出价
                        print(f"跳过买入: 当前低点 ${low:.2f} 不低于最近卖出价格 ${last_sell_price:.2f}")
                        continue
                shares_to_buy = cash // low
                buy_value = shares_to_buy * low
                if shares_to_buy > 0:
                    cash -= buy_value + fee
                    total_fees += fee
                    shares += shares_to_buy
                    trades.append({
                        "action": "buy",
                        "price": low,
                        "shares": shares_to_buy,
                        "amount": buy_value,
                        "cash_after": cash,
                        "fee": fee,
                        "date": date
                    })
                    print(f"买入触发: 股价 ${low:.2f}, 数量 {shares_to_buy:.2f}, 总金额 ${buy_value:.2f}, 现金余额 ${cash:.2f}")

        # 最后一天清仓
        if shares > 0:
            last_close_price = float(self.data['Close'].iloc[-1])
            sell_value = shares * last_close_price
            cash += sell_value - fee
            total_fees += fee
            trades.append({
                "action": "sell",
                "price": last_close_price,
                "shares": shares,
                "amount": sell_value,
                "cash_after": cash,
                "fee": fee,
                "date": self.data.index[-1].strftime('%Y-%m-%d')
            })
            print(f"最后一天清仓: 股价 ${last_close_price:.2f}, 数量 {shares:.2f}, 总金额 ${sell_value:.2f}, 现金余额 ${cash:.2f}")

        profit = cash - initial_investment
        return profit, cash, trades, total_fees

if __name__ == "__main__":
    # 用户输入
    stock_code = input("请输入股票代码 (例如: NVDA): ").strip().upper()
    start_date = input("请输入开始日期 (格式: YYYY-MM-DD，默认2024-01-02): ") or "2024-01-02"
    end_date = input("请输入结束日期 (格式: YYYY-MM-DD，默认今天): ") or datetime.now().strftime('%Y-%m-%d')
    initial_investment = input("请输入初始投资金额 (例如: 10000，默认10000): ")
    initial_investment = float(initial_investment) if initial_investment else 10000
    new_high_percentage = input("请输入创新高卖出要求的提升百分比 (例如: 5，默认5): ")
    new_high_percentage = float(new_high_percentage) if new_high_percentage else 5

    # 初始化分析器
    analyzer = StockAnalyzer(stock_code, start_date, end_date)

    # 高卖低买策略
    trading_profit, final_value_trading, trades, total_fees = analyzer.calculate_trading_strategy(
        initial_investment, new_high_percentage=new_high_percentage)
    print(f"\n高卖低买策略: 盈利 ${trading_profit:.2f}, 最终价值 ${final_value_trading:.2f}")
    print(f"总交易手续费: ${total_fees:.2f}")
    print("\n交易详情 (高卖低买策略):")
    for trade in trades:
        action = "买入" if trade["action"] == "buy" else "卖出"
        print(f"{trade['date']}: {action} - 股价 ${trade['price']:.2f}, 数量 {trade['shares']:.2f}, "
              f"金额 ${trade['amount']:.2f}, 现金余额 ${trade['cash_after']:.2f}, 手续费 ${trade['fee']:.2f}")

    # 买入并持有策略
    buy_and_hold_profit, final_value_hold, hold_trades = analyzer.calculate_buy_and_hold(initial_investment)
    print(f"\n买入并持有策略: 盈利 ${buy_and_hold_profit:.2f}, 最终价值 ${final_value_hold:.2f}")
    print("交易详情 (买入并持有策略):")
    for trade in hold_trades:
        print(f"{trade['action'].capitalize()}: 股价 ${trade['price']:.2f}, 数量 {trade['shares']:.2f} 股, "
              f"金额 ${trade['amount']:.2f}, 手续费 ${trade['fee']:.2f}")

    # 对比收益率
    print("\n最优方案对比:")
    if trading_profit > buy_and_hold_profit:
        difference = (trading_profit - buy_and_hold_profit) / abs(buy_and_hold_profit) * 100
        print(f"高卖低买策略更优，收益率高出 {difference:.2f}%。")
    elif trading_profit < buy_and_hold_profit:
        difference = (buy_and_hold_profit - trading_profit) / abs(trading_profit) * 100
        print(f"买入并持有策略更优，收益率高出 {difference:.2f}%。")
    else:
        print("两种策略收益相同。")
