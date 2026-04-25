import yfinance as yf
import time
import csv
import os
import json
from datetime import datetime, timedelta
from notifiers import send_telegram_msg

# Configuration
LOG_FILE = "trade_history.csv"
WATCHLIST_FILE = "price_alert_bot/watchlist.json"
WINRATE_THRESHOLD = 3.0
WINRATE_DAYS = 5

def log_alert(symbol, alert_type, price, target=None):
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'symbol', 'type', 'price', 'target', 'status'])
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), symbol, alert_type, price, target, 'PENDING'])

def check_price_target(symbol, target_price, side="above"):
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d")
        if data.empty: return False
        current_price = data['Close'].iloc[-1]
        
        hit = False
        if side == "above" and current_price >= target_price: hit = True
        elif side == "below" and current_price <= target_price: hit = True
            
        if hit:
            msg = f"🎯 TARGET HIT: {symbol} at {current_price:,.2f}"
            send_telegram_msg(msg)
            log_alert(symbol, f"TARGET_{side.upper()}", current_price, target_price)
            return True
    except: pass
    return False

def check_price_drop(symbol, threshold_percent):
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d")
        if data.empty: return False
        open_price = data['Open'].iloc[-1]
        current_price = data['Close'].iloc[-1]
        change_percent = ((current_price - open_price) / open_price) * 100
        
        if change_percent <= threshold_percent:
            msg = f"🔴 DROP ALERT: {symbol} ({change_percent:.2f}%)"
            send_telegram_msg(msg)
            log_alert(symbol, "DROP", current_price, threshold_percent)
            return True
    except: pass
    return False

import requests
import ollama

# Configuration
LOG_FILE = "trade_history.csv"
WATCHLIST_FILE = "price_alert_bot/watchlist.json"
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
last_update_id = 0

def get_tars_reply(user_msg):
    """Universal Agentic Loop for Telegram with Precision Tools"""
    now = datetime.now()
    today_str = now.strftime("%A, %B %d, %Y")
    time_str = now.strftime("%H:%M")
    
    local_history = [{"role": "user", "content": user_msg}]
    final_output = ""
    
    for i in range(3):
        agent_instruction = (
            "You are K2, a tactical droid assistant.\n\n"
            "IDENTITY: Blunt, dry, sarcastic. Never warm. Never chatty.\n\n"
            "RESPONSE FORMAT — strictly follow this order:\n"
            "1. Call the required tool(s)\n"
            "2. Read the RESULT\n"
            "3. Output the data in one line: \"SYMBOL: VALUE.\"\n"
            "4. Add ONE sarcastic sentence maximum\n"
            "5. Output DONE. Stop immediately. No more text.\n\n"
            "TOOLS YOU HAVE (use ONLY these, no others):\n"
            "- <call:fetch_price symbol=\"SYMBOL\" /> — gets stock or crypto price\n"
            "- <call:fetch_weather city=\"CITY\" /> — gets weather\n"
            "- <call:get_date offset=\"N\" /> — gets date (offset=0 for today)\n\n"
            "STRICT RULES:\n"
            "- Never call a tool that is not in the list above\n"
            "- Never guess or fabricate data\n"
            "- Never give financial advice\n"
            "- Never explain what you cannot do — just answer what you can\n"
            "- DONE ends every response, no exceptions"
        )
        
        # Adjusting regex for Telegram to match the new <call> format
        messages = [{"role": "system", "content": agent_instruction}] + local_history
        
        try:
            response = ollama.chat(model='hermes3', messages=messages)
            content = response['message']['content']
            
            import re
            call_match = re.search(r"<call:(\w+)\s+(.*?)\s*/>", content.lower())
            
            if call_match:
                tool_name, args_raw = call_match.groups()
                arg_val = re.search(r'="?([^"]*)"?', args_raw)
                val = arg_val.group(1) if arg_val else ""
                
                result = "ERROR: Unknown tool."
                if tool_name == "get_date":
                    try:
                        # Use 'val' which is already parsed from the tag
                        clean_val = re.sub(r"[^0-9-]", "", val) if val else "0"
                        offset = int(clean_val) if clean_val else 0
                        target = datetime.now() + timedelta(days=offset)
                        result = f"RESULT: {target.strftime('%A, %B %d, %Y')}"
                    except: result = "ERROR: Invalid offset. Use a number."
                elif tool_name == "calculate":
                    try: 
                        expr = val.replace("'", "").replace("\"", "")
                        result = f"RESULT: {eval(expr)}"
                    except: result = "ERROR: Math failed."
                elif tool_name == "fetch_price":
                    import yfinance as yf
                    try:
                        ticker = val.strip().upper()
                        # Simple crypto mapping
                        if ticker == "BTC": ticker = "BTC-USD"
                        if ticker == "ETH": ticker = "ETH-USD"
                        t = yf.Ticker(ticker)
                        p = t.history(period="1d")['Close'].iloc[-1]
                        result = f"RESULT: {ticker} is {p:,.2f}."
                    except: result = f"ERROR: Could not fetch {val}."
                elif tool_name == "fetch_weather":
                    import requests
                    try:
                        url = f"https://wttr.in/{val.strip()}?format=3"
                        result = f"RESULT: {requests.get(url).text}"
                    except: result = "ERROR: Weather offline."
                elif tool_name == "read_log":
                    try:
                        n = int(re.sub(r"[^0-9]", "", val)) if val else 5
                        with open(LOG_FILE, "r") as f:
                            result = "RESULT: " + "".join(f.readlines()[-n:])
                    except: result = "ERROR: Log not found."
                elif tool_name == "add_alert":
                    try:
                        with open(WATCHLIST_FILE, "r+") as f:
                            data = json.load(f)
                            data["alerts"].append({"symbol": args[0], "type": args[1], "threshold": float(args[2])})
                            f.seek(0); json.dump(data, f, indent=2); f.truncate()
                        result = f"RESULT: Alert for {args[0]} added."
                    except: result = "ERROR: Watchlist update failed."

                # CRITICAL FIX: Use 'user' role with explicit tag for tool results
                local_history.append({"role": "assistant", "content": content})
                local_history.append({"role": "user", "content": f"[TOOL RESULT] {result}"})
                print(f"  🤖 K2 used {tool_name}: {result}")
            else:
                final_output = content
                break
        except Exception as e:
            return f"Logic Error: {e}"
            
    return f"{final_output}\n\n<i>[Process: Agentic Loop]</i>"

def send_telegram_msg(message, chat_id=CHAT_ID):
    """Enhanced to allow sending to different chats (like groups)"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload)
    except: pass

def handle_telegram_commands():
    """Check for new messages and reply to the same chat they came from"""
    global last_update_id
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_update_id + 1}"
    try:
        updates = requests.get(url).json()
        if updates.get("ok") and updates.get("result"):
            for update in updates["result"]:
                last_update_id = update["update_id"]
                msg = update.get("message", {}) or update.get("edited_message", {})
                text = msg.get("text")
                current_chat_id = str(msg.get("chat", {}).get("id"))
                
                if text:
                    print(f"📥 Received from ID {current_chat_id}: {text}")
                    reply = get_tars_reply(text)
                    # We reply to current_chat_id (the group or personal chat)
                    send_telegram_msg(reply, chat_id=current_chat_id)
    except Exception as e:
        print(f"Listener Error: {e}")

if __name__ == "__main__":
    print("🚀 Jedi Price Monitor & Two-Way K2 Active...")
    while True:
        # 1. Listen for Telegram Commands
        handle_telegram_commands()
        
        # 2. (Existing) Scan prices from Watchlist
        # ... (rest of logic)
