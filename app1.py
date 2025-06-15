import streamlit as st
from binance.client import Client
import pandas as pd
import numpy as np
import datetime as dt
import yfinance as yf
import requests
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator

# ========== Setup API ==========
API_KEY = st.secrets["API_KEY"]
API_SECRET = st.secrets["API_SECRET"]
NEWS_API = st.secrets["NEWS_API"]

client = Client(API_KEY, API_SECRET)

st.set_page_config(layout="wide")
st.title("📈 Sistem Analisa Trading Otomatis")
st.markdown("Tekan tombol di bawah untuk mendapatkan analisa real-time dari 5 pair terbaik di Binance.")

if st.button("🚀 Mulai Analisa Trading"):

    # ========== Ambil Data Pasar ==========
    st.subheader("📊 5 Pair Terbaik Saat Ini")

    tickers = [s['symbol'] for s in client.get_ticker_24hr() if s['symbol'].endswith('USDT')]
    top_pairs = sorted(client.get_ticker_24hr(), key=lambda x: float(x['priceChangePercent']), reverse=True)
    top_5 = [pair['symbol'] for pair in top_pairs[:5] if pair['symbol'].endswith('USDT')]

    for symbol in top_5:
        try:
            st.markdown(f"---\n### 🪙 {symbol}")

            df = pd.DataFrame(client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_15MINUTE, limit=100),
                            columns=['Time','Open','High','Low','Close','Volume','Close time','Quote asset volume','Num trades','Taker buy base asset vol','Taker buy quote asset vol','Ignore'])

            df['Close'] = df['Close'].astype(float)
            df['Time'] = pd.to_datetime(df['Time'], unit='ms')

            rsi = RSIIndicator(close=df['Close']).rsi().iloc[-1]
            sma = SMAIndicator(close=df['Close'], window=20).sma_indicator().iloc[-1]
            macd = MACD(close=df['Close']).macd_diff().iloc[-1]
            last_price = df['Close'].iloc[-1]

            trend = "Bullish" if macd > 0 and rsi > 50 else "Bearish" if macd < 0 and rsi < 50 else "Sideways"
            confidence = int(np.clip((abs(rsi - 50) + abs(macd)) * 1.5, 0, 100))

            # ========== Saran Entry / SL / TP ==========
            entry_price = round(last_price, 4)
            stop_loss = round(entry_price * 0.98, 4)
            take_profit = round(entry_price * 1.03, 4)

            # ========== Saran Metode ==========
            method = "Scalping" if trend == "Sideways" else "Grid Trading"
            timing = (dt.datetime.now() + dt.timedelta(minutes=30)).strftime("%H:%M")

            st.write(f"**Harga Sekarang:** ${entry_price}")
            st.write(f"**RSI:** {round(rsi, 2)} | **MACD:** {round(macd, 4)} | **MA20:** {round(sma, 4)}")
            st.write(f"**Trend:** {trend} | **Confidence:** {confidence}%")
            st.write(f"**Saran Entry:** {entry_price} | **TP:** {take_profit} | **SL:** {stop_loss}")
            st.write(f"**Jenis Trading:** Spot / Futures")
            st.write(f"**Strategi:** {method}")
            st.write(f"**Berlaku hingga:** {timing} WIB")

            if method == "Grid Trading":
                st.caption("🟢 Grid: 3-5 level | Range: ±1.5% dari harga | Modal per grid: 20% dari modal total")

        except Exception as e:
            st.warning(f"Gagal analisa {symbol}: {e}")

    # ========== Berita Fundamental ==========
    st.subheader("📰 Berita Crypto Terkini")
    try:
        url = f"https://newsapi.org/v2/everything?q=crypto&sortBy=publishedAt&language=en&pageSize=3&apiKey={NEWS_API}"
        news = requests.get(url).json()

        for article in news['articles']:
            st.markdown(f"**{article['title']}**")
            st.markdown(f"*{article['source']['name']}* - {article['publishedAt'][:10]}")
            st.markdown(article['description'] or "")
            st.markdown(f"[🔗 Baca selengkapnya]({article['url']})\n")

    except Exception as e:
        st.error(f"Gagal mengambil berita: {e}")

    st.success("✅ Analisa selesai.")
