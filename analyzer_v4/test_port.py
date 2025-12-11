import socket

def test_port(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        result = sock.connect_ex((host, port))
        if result == 0:
            print(f"✅ 端口 {port} 已开放")
        else:
            print(f"❌ 端口 {port} 未开放")
    except Exception as e:
        print(f"❌ 测试端口 {port} 时出错: {str(e)}")
    finally:
        sock.close()

print("测试TWS端口 (7496)...")
test_port('127.0.0.1', 7496)

print("\n测试Gateway端口 (7497)...")
test_port('127.0.0.1', 7497) 