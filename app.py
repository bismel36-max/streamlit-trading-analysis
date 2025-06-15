import streamlit as st
import pandas as pd
import numpy as np
from binance.client import Client
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
from datetime import datetime, timedelta
import requests, yfinance as yf

# API Binance (gunakan akunmu sendiri)
API_KEY = 'S0SwKgYmE9Hk29U7RH6ad64qkO5wc5CUIrz33jh7iVFRURiDpJAvGw6qN1hT9u7F'
API_SECRET = 'VO0r6C3Glscilr7z0K00MZLR8n6poXxA4eC7Qfy5G2Hufqsu9VUatzvx9fAIQltj'
client = Client(API_KEY, API_SECRET)

st.set_page_config(layout="wide")
st.title("📊 Sistem Analisa Trading Profesional Binance")

def get_top_pairs(limit=5):
    tickers = client.get_ticker()
    usdt_pairs = [x for x in tickers if x['symbol'].endswith('USDT') and float(x['quoteVolume']) > 1000000]
    sorted_pairs = sorted(usdt_pairs, key=lambda x: float(x['quoteVolume']), reverse=True)
    return [p['symbol'] for p in sorted_pairs[:limit]]

def get_klines(symbol, interval='1h', limit=100):
    data = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'])
    df['close'] = df['close'].astype(float)
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def technical_analysis(df):
    ema = EMAIndicator(close=df['close'], window=20).ema_indicator().iloc[-1]
    macd = MACD(close=df['close']).macd_diff().iloc[-1]
    rsi = RSIIndicator(close=df['close']).rsi().iloc[-1]
    bb = BollingerBands(close=df['close'])
    bb_width = (bb.bollinger_hband() - bb.bollinger_lband()).iloc[-1]

    signal = []
    confidence = 0

    if df['close'].iloc[-1] > ema:
        signal.append("Uptrend")
        confidence += 20
    if macd > 0:
        signal.append("MACD Bullish")
        confidence += 25
    if rsi < 30:
        signal.append("Oversold")
        confidence += 25
    elif rsi > 70:
        signal.append("Overbought")
        confidence -= 25
    if bb_width < np.mean(bb.bollinger_hband() - bb.bollinger_lband()):
        signal.append("Squeeze (Sideways)")
    else:
        signal.append("Breakout Potential")
        confidence += 10

    return {
        "trend": ", ".join(signal),
        "rsi": round(rsi, 2),
        "confidence": min(100, max(0, confidence)),
        "entry": df['close'].iloc[-1],
        "sl": df['low'].iloc[-5],
        "tp": df['close'].iloc[-1] * 1.02,
        "recommend": "Long" if confidence > 50 else "Wait",
        "suggestion": "Scalping" if confidence >= 60 else "Grid",
        "grid_param": {
            "range": f"{round(df['low'].min(), 4)} - {round(df['high'].max(), 4)}",
            "grids": 5
        },
        "valid_until": (datetime.now() + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M'),
    }

def get_news():
    try:
        r = requests.get("https://newsapi.org/v2/everything?q=crypto&apiKey=PASTE_NEWSAPI_KEY_HERE")
        data = r.json()
        headlines = [article['title'] for article in data['articles'][:3]]
        return headlines
    except:
        return ["Berita tidak tersedia (ganti API Key)"]

# UI
if st.button("🚀 Mulai Analisa Trading"):
    pairs = get_top_pairs()
    for symbol in pairs:
        st.subheader(f"📈 Pair: {symbol}")
        df = get_klines(symbol)
        analysis = technical_analysis(df)

        col1, col2, col3 = st.columns(3)
        col1.metric("Trend", analysis['trend'], f"RSI: {analysis['rsi']}")
        col2.metric("Confidence", f"{analysis['confidence']}%", "🧠")
        col3.metric("Rekomendasi", analysis['recommend'])

        st.write(f"💡 Entry: `{analysis['entry']}` | SL: `{round(analysis['sl'],4)}` | TP: `{round(analysis['tp'],4)}`")
        st.write(f"🧭 Rekomendasi Trading: `{analysis['suggestion']}`")
        if analysis['suggestion'] == "Grid":
            st.write(f"🧮 Grid Parameter: Range {analysis['grid_param']['range']}, Grid: {analysis['grid_param']['grids']}")
        st.info(f"📅 Analisa berlaku sampai: {analysis['valid_until']}")

        # Fundamental analysis (YFinance)
        yf_ticker = yf.Ticker(symbol.replace("USDT", "-USD"))
        info = yf_ticker.info
        if 'longBusinessSummary' in info:
            st.write(f"📌 Fundamental: {info['longBusinessSummary'][:400]}...")

    st.subheader("🌐 Berita Fundamental Terkini")
    for news in get_news():
        st.write("• " + news)
