import requests
from datetime import datetime


def get_candles(symbol='BTCUSDT', interval='1m', limit=60):
    url = f"https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    res = requests.get(url, params=params)
    res.raise_for_status()

    data = res.json()
    candles = []
    for item in data:
        candles.append({
            "time": datetime.fromtimestamp(item[0] / 1000),
            "open": float(item[1]),
            "high": float(item[2]),
            "low": float(item[3]),
            "close": float(item[4]),
        })
    return candles
