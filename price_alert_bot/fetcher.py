import yfinance as yf
import requests

def get_crypto_price(symbol="bitcoin"):
    """ดึงราคา Crypto จาก CoinGecko (ฟรีไม่ต้องมี API Key)"""
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd"
    response = requests.get(url).json()
    return response[symbol]['usd']

def get_market_price(ticker_symbol):
    """ดึงราคาหุ้นไทย, ETF, หรือ Gold จาก Yahoo Finance"""
    # หุ้นไทยต้องเติม .BK เช่น PTT.BK, ETF ใช้ชื่อปกติเช่น QQQM, ทองใช้ GC=F
    ticker = yf.Ticker(ticker_symbol)
    data = ticker.history(period="1d")
    return round(data['Close'].iloc[-1], 2)

if __name__ == "__main__":
    print("--- 📊 กำลังดึงข้อมูลราคาล่าสุด ---")
    
    # ดึงราคา BTC
    btc = get_crypto_price("bitcoin")
    print(f"₿ Bitcoin: ${btc:,}")

    # ดึงราคาทอง (Gold Futures)
    gold = get_market_price("GC=F")
    print(f"🥇 Gold Futures: ${gold:,}")

    # ดึงราคาหุ้นไทย (ตัวอย่าง PTT)
    ptt = get_market_price("PTT.BK")
    print(f"📈 PTT (Thai Stock): ฿{ptt}")

    # ดึงราคา ETF (ตัวอย่าง QQQM ที่คุณ Wanakorn สนใจ)
    qqqm = get_market_price("QQQM")
    print(f"🇺🇸 QQQM ETF: ${qqqm}")
