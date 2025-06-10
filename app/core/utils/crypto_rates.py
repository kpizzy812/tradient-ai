import aiohttp
from loguru import logger
from app.state import set_token_rate

TTL = 300  # 5 минут

async def fetch_token_price(symbol: str, vs_currency: str = "usd") -> float | None:

    COINGECKO_IDS = {
        "TON": "the-open-network",
        "USDT": "tether",
        "TRX": "tron",
        "RUB": "russian-ruble",
    }

    coingecko_id = COINGECKO_IDS.get(symbol.upper())
    if not coingecko_id:
        logger.warning(f"[RATES] ❌ Неизвестный токен: {symbol}")
        return None

    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": coingecko_id,
        "vs_currencies": vs_currency
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    price = data[coingecko_id][vs_currency]
                    await set_token_rate(f"{symbol.upper()}_{vs_currency.upper()}", float(price))
                    logger.info(f"[RATES] ✅ {symbol}/{vs_currency.upper()} = {price}")
                    return price
    except Exception as e:
        logger.warning(f"[RATES] ❌ Ошибка запроса CoinGecko: {e}")
    return None
