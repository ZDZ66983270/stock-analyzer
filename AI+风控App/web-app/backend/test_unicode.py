def test_decode():
    # Attempt 1: Raw string resembling what we get
    raw_name = r"\u4e2d\u8fdc\u6d77\u63a7" 
    print(f"Raw: {raw_name}")
    
    try:
        decoded = raw_name.encode('utf-8').decode('unicode_escape')
        print(f"Decoded: {decoded}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_decode()
