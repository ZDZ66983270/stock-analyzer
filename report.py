import requests

# 请求用户输入股票代码
stock_symbol = input("请输入股票代码: ").upper()

# 设置 Alpha Vantage API 的 URL（请替换为您的 API 密钥）
api_key = 'your_api_key_here'
url = f'https://www.alphavantage.co/query?function=INSIDER_TRANSACTIONS&symbol={stock_symbol}&apikey={api_key}'

# 发送请求并获取数据
response = requests.get(url)
data = response.json()

# 检查是否成功获取数据并将其保存到本地文件
if "transactions" in data:
    # 定义文件名
    file_name = f"{stock_symbol}_insider_transactions.txt"
    
    # 将数据写入文件
    with open(file_name, 'w') as file:
        file.write(f"{stock_symbol} 内部交易数据:\n\n")
        for transaction in data["transactions"]:
            file.write(str(transaction) + '\n')
    print(f"数据已成功保存到 {file_name}")
else:
    print("未能获取数据，请检查股票代码或API密钥。")
