from ib_insync import *
import time
import xml.etree.ElementTree as ET

def test_ib_valuation_history():
    print("🚀 Connecting to IB (Port 7497)...")
    ib = IB()
    try:
        ib.connect('127.0.0.1', 7497, clientId=6) 
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return

    print("✅ Connected!")

    stock = Stock('TSLA', 'SMART', 'USD')
    
    report_types = ['ReportsFinSummary', 'RESC', 'ReportsFinStatements']
    
    for report_type in report_types:
        print(f"\n📋 Requesting '{report_type}' for {stock.symbol}...")
        try:
            xml_data = ib.reqFundamentalData(stock, report_type)
            if xml_data:
                print(f"✅ {report_type} Received! ({len(xml_data)} bytes)")
                try:
                    root = ET.fromstring(xml_data)
                    # Just print first few tags to show structure
                    print(f"   Root Tag: {root.tag}")
                    children = list(root)[:5]
                    print(f"   Children: {[c.tag for c in children]}")
                except:
                    pass
            else:
                print(f"⚠️ {report_type} returned empty.")
        except Exception as e:
            print(f"❌ {report_type} failed: {e}")
        
        time.sleep(2) # Pause between requests

    ib.disconnect()

if __name__ == "__main__":
    test_ib_valuation_history()
