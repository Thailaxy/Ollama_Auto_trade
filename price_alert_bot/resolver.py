import csv
import os
import yfinance as yf
from datetime import datetime
import tempfile
import shutil

HISTORY_FILE = "price_alert_bot/trade_history.csv"

def get_current_price(symbol):
    """Helper to fetch price for resolution"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d")
        if not data.empty:
            return data['Close'].iloc[-1]
    except:
        pass
    return None

def resolve_trades():
    if not os.path.exists(HISTORY_FILE) or os.path.getsize(HISTORY_FILE) == 0:
        print("ℹ️ No trade history to resolve.")
        return

    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, newline='')
    updated = False
    
    today = datetime.now().date()
    
    with open(HISTORY_FILE, 'r') as f, temp_file:
        reader = csv.DictReader(f)
        writer = csv.DictWriter(temp_file, fieldnames=reader.fieldnames)
        writer.writeheader()
        
        for row in reader:
            if row['status'] == 'PENDING':
                resolve_date_str = row.get('days_to_resolve')
                if resolve_date_str:
                    resolve_date = datetime.strptime(resolve_date_str, "%Y-%m-%d").date()
                    
                    # If target date has arrived or passed
                    if today >= resolve_date:
                        symbol = row['symbol']
                        current_price = get_current_price(symbol)
                        
                        if current_price is not None:
                            price_at_alert = float(row['price_at_alert'])
                            alert_type = row['alert_type']
                            status = "LOSS"
                            
                            # WIN CONDITION LOGIC
                            if alert_type == "DROP" or alert_type == "TARGET_BELOW":
                                # WIN if price recovered > 2% from the alert price
                                if current_price >= (price_at_alert * 1.02):
                                    status = "WIN"
                            elif alert_type == "RISE" or alert_type == "TARGET_ABOVE":
                                # WIN if price continued to rise or stayed above threshold
                                if current_price >= float(row['threshold']):
                                    status = "WIN"
                            
                            row['status'] = status
                            row['result'] = f"{current_price:,.2f}"
                            updated = True
                            print(f"✅ Resolved {symbol}: {status} (Price: {current_price:,.2f})")

            writer.writerow(row)

    if updated:
        shutil.move(temp_file.name, HISTORY_FILE)
        print("📝 trade_history.csv updated in-place.")
    else:
        os.remove(temp_file.name)
        print("💤 No rows reached resolution date yet.")

if __name__ == "__main__":
    print("🛰️ K2 Resolver Engine Starting...")
    resolve_trades()
