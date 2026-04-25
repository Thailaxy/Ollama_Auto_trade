import requests

# แทนที่ด้วยข้อมูลที่คุณก๊อปปี้มา
TOKEN = "8658926505:AAGdJcNJ38CHkEjdCZfndN5xDzNFXe98lD0"
CHAT_ID = "6128986691"

def send_telegram_msg(message):
    """ฟังก์ชันส่งข้อความเข้า Telegram"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML" # เพื่อให้แต่งตัวหนา/ตัวเอียงได้
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("✅ ส่งข้อความสำเร็จ!")
        else:
            print(f"❌ ส่งไม่สำเร็จ: {response.text}")
    except Exception as e:
        print(f"⚠️ เกิดข้อผิดพลาด: {e}")

if __name__ == "__main__":
    # ทดสอบส่งข้อความแรก
    test_msg = "🚀 <b>Wanakorn Bot Online!</b>\nSystem is now online and monitoring stock prices."
    send_telegram_msg(test_msg)
