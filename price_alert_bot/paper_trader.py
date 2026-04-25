"""
###############################################################################
#                           PAPER TRADING ONLY                                #
#    This module simulates trades for educational and analytics purposes.     #
#    NO REAL ASSETS ARE BOUGHT OR SOLD.                                       #
###############################################################################
"""

import csv
import os
from datetime import datetime

TRADES_FILE = "price_alert_bot/paper_trades.csv"

def execute_paper_trade(symbol, alert_type, price, alert_timestamp):
    """
    Simulates a trade based on alert logic.
    - DROP alert → BUY
    - RISE alert → SELL  
    - TARGET_ABOVE → SELL
    - TARGET_BELOW → BUY
    """
    action = ""
    if alert_type == "DROP" or alert_type == "TARGET_BELOW":
        action = "BUY"
    elif alert_type == "RISE" or alert_type == "TARGET_ABOVE":
        action = "SELL"
    
    if not action:
        return
        
    # quantity = round(100 / price, 4)
    try:
        quantity = round(100.0 / float(price), 4)
    except (ZeroDivisionError, ValueError):
        quantity = 0
        
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    file_exists = os.path.isfile(TRADES_FILE)
    headers = ['timestamp', 'symbol', 'action', 'price', 'quantity', 'reason', 'alert_timestamp']
    
    with open(TRADES_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists or os.path.getsize(TRADES_FILE) == 0:
            writer.writerow(headers)
        writer.writerow([
            timestamp, symbol, action, price, quantity, f"Triggered by {alert_type}", alert_timestamp
        ])
    
    print(f"📦 Paper Trade Executed: {action} {quantity} {symbol} @ {price}")

if __name__ == "__main__":
    # Standalone test execution
    # execute_paper_trade("BTC-USD", "DROP", 77000.0, "2026-04-25 15:00:00")
    pass
