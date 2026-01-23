import akshare as ak

def test_legu():
    print("Testing ak.stock_a_indicator_lg(symbol='000001')...")
    try:
        df = ak.stock_a_indicator_lg(symbol="000001")
        if df is not None:
             print("Columns:", list(df.columns))
             print(df.tail(1))
        else:
            print("Returned None")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_legu()
