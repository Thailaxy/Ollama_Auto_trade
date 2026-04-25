import yfinance as yf
import requests
import json
import time
import csv
import os
from datetime import datetime, timedelta
from paper_trader import execute_paper_trade

# --- CONFIGURATION (via Environment Variables) ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
WATCHLIST_FILE = "price_alert_bot/watchlist.json"
HISTORY_FILE = "price_alert_bot/trade_history.csv"

# Global cooldown set to prevent alert spam
triggered_today = set()

# --- CORE FUNCTIONS ---

def send_telegram(message):
    if not TOKEN or not CHAT_ID:
        print("⚠️ Telegram credentials missing in environment variables.")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

def log_trade(symbol, asset_class, alert_type, threshold, price):
    file_exists = os.path.isfile(HISTORY_FILE)
    headers = ['timestamp', 'symbol', 'asset_class', 'alert_type', 'threshold', 'price_at_alert', 'status', 'result', 'days_to_resolve']
    
    # Calculate target resolve date (5 days from now)
    resolve_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(HISTORY_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists or os.path.getsize(HISTORY_FILE) == 0:
            writer.writerow(headers)
        writer.writerow([
            ts, symbol, asset_class, alert_type, threshold, price, 'PENDING', '', resolve_date
        ])
    return ts

def get_crypto_price(coin_id):
    """Fetch crypto price via CoinGecko (Free API)"""
    try:
        # Mapping common tickers to CoinGecko IDs if necessary
        mapping = {"BTC": "bitcoin", "ETH": "ethereum", "BTC-USD": "bitcoin", "ETH-USD": "ethereum"}
        cid = mapping.get(coin_id.upper(), coin_id.lower())
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={cid}&vs_currencies=usd"
        res = requests.get(url, timeout=10).json()
        return res[cid]['usd']
    except: return None

def get_market_price(symbol):
    """Fetch stock price (Thai or World) via yfinance"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d")
        if data.empty: return None
        return data['Close'].iloc[-1], data['Open'].iloc[-1]
    except: return None, None

def recalculate_targets(symbol, triggered_price):
    """After a TARGET alert fires, reset thresholds to +-2.5% 
    from the new price so watchlist stays current automatically."""
    try:
        with open(WATCHLIST_FILE, 'r') as f:
            watchlist = json.load(f)
        
        new_below = round(triggered_price * 0.975, 2)
        new_above = round(triggered_price * 1.025, 2)
        
        for alert in watchlist["alerts"]:
            if alert["symbol"] == symbol:
                if alert["type"] == "TARGET_BELOW":
                    alert["threshold"] = new_below
                elif alert["type"] == "TARGET_ABOVE":
                    alert["threshold"] = new_above
        
        with open(WATCHLIST_FILE, 'w') as f:
            json.dump(watchlist, f, indent=2)
        
        print(f"📐 {symbol} targets recalculated: BELOW={new_below}, ABOVE={new_above}")
    except Exception as e:
        print(f"Error recalculating targets: {e}")

def monitor():
    print(f"🚀 K2 Monitor Active: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not os.path.exists(WATCHLIST_FILE):
        print("⚠️ No watchlist found.")
        return

    with open(WATCHLIST_FILE, 'r') as f:
        watchlist = json.load(f).get("alerts", [])

    for alert in watchlist:
        symbol = alert['symbol']
        a_type = alert['type']
        threshold = float(alert['threshold'])
        
        # Determine Asset Class
        asset_class = "STOCK_WORLD"
        if symbol.endswith(".BK"): asset_class = "STOCK_THAI"
        elif any(c in symbol.upper() for c in ["BTC", "ETH"]): asset_class = "CRYPTO"

        # Fetch Price
        current_price = None
        open_price = None
        
        if asset_class == "CRYPTO":
            current_price = get_crypto_price(symbol)
        else:
            current_price, open_price = get_market_price(symbol)

        if current_price is None:
            print(f"❌ Failed to fetch {symbol}")
            continue

        # Check Logic
        triggered = False
        change_pct = 0
        if open_price:
            change_pct = ((current_price - open_price) / open_price) * 100

        if a_type == "DROP" and change_pct <= threshold: triggered = True
        elif a_type == "RISE" and change_pct >= threshold: triggered = True
        elif a_type == "TARGET_ABOVE" and current_price >= threshold: triggered = True
        elif a_type == "TARGET_BELOW" and current_price <= threshold: triggered = True

        if triggered:
            # Check cooldown set to prevent spam
            alert_key = f"{symbol}_{a_type}_{datetime.now().date()}"
            if alert_key not in triggered_today:
                msg = (f"📡 <b>K2 ALERT: {symbol}</b>\n"
                       f"Price: {current_price:,.2f}\n"
                       f"Trigger: {a_type} ({threshold})\n"
                       f"Status: Logged to Archive.")
                send_telegram(msg)
                ts = log_trade(symbol, asset_class, a_type, threshold, current_price)
                execute_paper_trade(symbol, a_type, current_price, ts)
                
                if a_type in ["TARGET_ABOVE", "TARGET_BELOW"]:
                    recalculate_targets(symbol, current_price)
                    
                triggered_today.add(alert_key)
                print(f"🎯 Alert triggered and logged for {symbol}")
            else:
                print(f"ℹ️ Alert for {symbol} ({a_type}) already sent today. Skipping.")

if __name__ == "__main__":
    while True:
        try:
            monitor()
        except Exception as e:
            print(f"Loop Error: {e}")
        print("💤 Sleeping 5 minutes...")
        time.sleep(300)
