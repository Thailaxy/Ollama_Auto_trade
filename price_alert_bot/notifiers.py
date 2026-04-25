import requests
import os

# ดึงค่าจาก Environment Variables
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram_msg(message):
    """ฟังก์ชันส่งข้อความเข้า Telegram"""
    if not TOKEN or not CHAT_ID:
        print("⚠️ Telegram credentials missing.")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("✅ ส่งข้อความสำเร็จ!")
        else:
            print(f"❌ ส่งไม่สำเร็จ: {response.text}")
    except Exception as e:
        print(f"⚠️ เกิดข้อผิดพลาด: {e}")
