import os
import csv
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class LedgerManager:
    def __init__(self, ledger_file="update_ledger.csv"):
        self.ledger_file = os.path.join(os.path.dirname(__file__), ledger_file)
        self.ledger_data = {} # {symbol: last_update_date_str}
        self.load_ledger()

    def load_ledger(self):
        if not os.path.exists(self.ledger_file):
            # Init empty ledger
            with open(self.ledger_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['symbol', 'last_update', 'market', 'status'])
            return

        try:
            with open(self.ledger_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.ledger_data[row['symbol']] = row
        except Exception as e:
            logger.error(f"Error loading ledger: {e}")

    def get_last_update(self, symbol):
        """Returns last update date string or None"""
        record = self.ledger_data.get(symbol)
        if record:
            return record.get('last_update')
        return None

    def update_entry(self, symbol, market, date_str, status="Success"):
        """Update or Add entry"""
        self.ledger_data[symbol] = {
            'symbol': symbol,
            'last_update': date_str,
            'market': market,
            'status': status
        }
        self.save_ledger()

    def save_ledger(self):
        try:
            with open(self.ledger_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['symbol', 'last_update', 'market', 'status']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for sym, data in self.ledger_data.items():
                    writer.writerow(data)
        except Exception as e:
            logger.error(f"Error saving ledger: {e}")

# Usage Example
if __name__ == "__main__":
    lm = LedgerManager()
    print("Current Ledger:", lm.ledger_data)
    lm.update_entry("09988", "HK", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("Updated Ledger.")
