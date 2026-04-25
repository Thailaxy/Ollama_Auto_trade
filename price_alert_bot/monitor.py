import yfinance as yf
import time
from datetime import datetime, timedelta
from notifiers import send_telegram_msg

def check_24h_movement(symbol="BTC-USD", threshold=0.5):
    """เช็คการเคลื่อนไหวเทียบกับ 24 ชม. ที่แล้ว"""
    try:
        # ดึงข้อมูลย้อนหลัง 2 วัน เพื่อให้มั่นใจว่าครอบคลุมช่วง 24 ชม.
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="2d", interval="1m")

        if df.empty or len(df) < 1440: # 1440 คือจำนวนนาทีใน 24 ชม.
            print("⚠️ ข้อมูลไม่เพียงพอ กำลังรอรอบถัดไป...")
            return

        current_price = df['Close'].iloc[-1]
        price_24h_ago = df['Close'].iloc[-1440] # ย้อนไป 1440 แถว (1440 นาที)
        
        change_percent = ((current_price - price_24h_ago) / price_24h_ago) * 100
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {symbol}: ${current_price:,.2f} | Change 24h: {change_percent:+.2f}%")

        # เช็คว่าเคลื่อนไหวเกิน threshold (ใช้ abs เพื่อเช็คทั้งขึ้นและลง)
        if abs(change_percent) >= threshold:
            status_icon = "🚀" if change_percent > 0 else "🔴"
            direction = "พุ่งขึ้น" if change_percent > 0 else "ร่วงลง"
            
            msg = (f"{status_icon} <b>แจ้งเตือนความผันผวน {symbol}!</b>\n\n"
                   f"ราคาตอนนี้ {direction} เกิน {threshold}%\n"
                   f"ราคาปัจจุบัน: <b>${current_price:,.2f}</b>\n"
                   f"เทียบกับ 24 ชม. ก่อน: ${price_24h_ago:,.2f}\n"
                   f"เปลี่ยนแปลง: <b>{change_percent:+.2f}%</b>")
            
            send_telegram_msg(msg)
            return True
            
    except Exception as e:
        print(f"❌ {symbol} เกิดข้อผิดพลาด: {e}")
    
    return False

if __name__ == "__main__":
    print("🤖 WK Price Alert: Multi-Crypto Monitor Started...")
    print("------------------------------------------")
    
    # รายชื่อเหรียญที่ต้องการเช็ค
    symbols = ["BTC-USD", "ETH-USD"]
    
    # วนลูปทำงานตลอดเวลา
    while True:
        for sym in symbols:
            check_24h_movement(symbol=sym, threshold=0.5)
        
        # ให้บอทพัก 5 นาที (300 วินาที) ก่อนเช็คใหม่ เพื่อไม่ให้โดนแบน API
        print("💤 พัก 5 นาที...")
        time.sleep(300)
