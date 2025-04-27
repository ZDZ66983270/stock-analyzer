import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
import requests
from datetime import datetime
from matplotlib.dates import DayLocator, DateFormatter
import time
import os

# User input for stock codes and date range
hk_stock = input("Enter HK stock code (e.g., 0700.HK): ").upper()
cn_stock = input("Enter CN stock code (e.g., 000001.SS): ").upper()
start_date = input("Enter start date (YYYY-MM-DD, default: 2024-01-01): ")
end_date = input("Enter end date (YYYY-MM-DD, default: today): ")

# Default date setting
if not start_date:
    start_date = "2024-01-01"
if not end_date:
    end_date = datetime.today().strftime('%Y-%m-%d')

# Alpha Vantage API configuration
API_KEY = 'HDDEA7IVYCSEVFNW'  # Replace with your Alpha Vantage API key

# Function to get historical data for USD to HKD and USD to CNY with caching
def get_exchange_rate_data_with_cache(symbol, cache_file):
    # Check if cached file exists
    if os.path.exists(cache_file):
        print(f"Loading {symbol} data from cache.")
        df = pd.read_csv(cache_file, parse_dates=["Date"], index_col="Date")
        return df
    else:
        print(f"No cache found for {symbol}, downloading data...")

    # If no cache, download data
    url = f"https://www.alphavantage.co/query?function=FX_DAILY&from_symbol=USD&to_symbol={symbol}&apikey={API_KEY}&outputsize=full"
    response = requests.get(url)
    data = response.json()

    # Parse data and cache it
    if "Time Series FX (Daily)" in data:
        rates = []
        for date, rate_info in data["Time Series FX (Daily)"].items():
            rates.append([date, float(rate_info["4. close"])])
        df = pd.DataFrame(rates, columns=["Date", f"USD{symbol}"])
        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)
        df.sort_index(inplace=True)
        df.to_csv(cache_file)  # Save data to cache
        return df
    else:
        print(f"Unable to retrieve data for {symbol}, check API key or frequency limit.")
        return None

# Get exchange rates with caching
usd_hkd = get_exchange_rate_data_with_cache("HKD", "usd_hkd_cache.csv")
time.sleep(12)  # Delay between requests to avoid hitting rate limit
usd_cny = get_exchange_rate_data_with_cache("CNY", "usd_cny_cache.csv")

# Check if data was successfully downloaded
if usd_hkd is None or usd_cny is None:
    exit()

# Merge data and calculate HKDCNY exchange rate
exchange_data = pd.concat([usd_hkd, usd_cny], axis=1).dropna()
exchange_data["HKDCNY"] = exchange_data["USDCNY"] / exchange_data["USDHKD"]

# Remove timezone information from index
exchange_data.index = exchange_data.index.tz_localize(None)

# Download stock data (daily)
data = yf.download([hk_stock, cn_stock], start=start_date, end=end_date, interval="1d")

# Check if data was successfully downloaded
if data.empty or len(data.columns.levels[1]) < 2:
    print("Failed to download CN or HK stock data, check stock codes and date range.")
    exit()

# Select adjusted close prices and print for debugging
adj_close = data['Adj Close']
print(f"Available adjusted close columns: {adj_close.columns}")

if hk_stock not in adj_close.columns or cn_stock not in adj_close.columns:
    print("Missing adjusted close prices for CN or HK stock, check stock codes.")
    exit()

# Remove timezone from adj_close Date column
adj_close = adj_close.reset_index()
adj_close['Date'] = adj_close['Date'].dt.tz_localize(None)

# Merge stock data and exchange rate data
merged_data = pd.merge(adj_close, exchange_data[["HKDCNY"]], left_on="Date", right_index=True, how="inner")
merged_data.set_index("Date", inplace=True)

# Calculate H-Share to A-Share ratio without exchange rate adjustment
merged_data["Discount Ratio"] = (merged_data[hk_stock] / merged_data[cn_stock]) * 100

# Calculate and print average exchange rate (HKD/CNY) as percentage
average_rate = merged_data["HKDCNY"].mean()
average_rate_percentage = average_rate * 100
print(f"Average exchange rate over period (HKD/CNY): {average_rate:.4f} ({average_rate_percentage:.2f}%)")

# Set default font to ensure English display
plt.rcParams['font.sans-serif'] = ['Arial']
plt.rcParams['axes.unicode_minus'] = False

# Plot Discount Ratio and HKDCNY Exchange Rate
fig, ax = plt.subplots(figsize=(12, 6))

# Plot Discount Ratio
ax.plot(merged_data.index, merged_data["Discount Ratio"], label=f"H-Share to A-Share Discount Ratio", color='blue', marker='o')

# Plot HKDCNY Exchange Rate
ax.plot(merged_data.index, merged_data["HKDCNY"] * 100, label="HKD to CNY Exchange Rate (%)", color='green', linestyle='-', alpha=0.7)

# Mark average exchange rate as a horizontal line
ax.axhline(average_rate_percentage, color='red', linestyle='--', linewidth=1, label=f"Average Exchange Rate: {average_rate_percentage:.2f}%")
ax.text(merged_data.index[-1], average_rate_percentage, f"{average_rate_percentage:.2f}%", ha='left', va='center', color='red')

# Label end of Discount Ratio line
end_value = merged_data["Discount Ratio"].iloc[-1]
ax.text(merged_data.index[-1], end_value, f"Current: {end_value:.2f}%", ha='left', color='blue')

# Set chart labels and title
ax.set_xlabel("Date (Daily)")
ax.set_ylabel("Percentage (%)")
ax.set_title(f"H-Share to A-Share Discount Ratio and HKD to CNY Exchange Rate (%)")
ax.legend(loc="upper left")
ax.grid()

# Adjust X-axis to show daily ticks
ax.xaxis.set_major_locator(DayLocator(interval=5))  # Major tick every 5 days
ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

plt.show()

# Print the comparison table
print("Comparison Table (Discount Ratio):")
print(merged_data[["Discount Ratio", "HKDCNY"]])
