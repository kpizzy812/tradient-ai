import random
import os
from datetime import datetime, timedelta, time as dtime
from sqlalchemy import func
from app.core.utils.binance import get_candles
from app.models.trades import Trade
from app.core.db import SessionLocal
from app.core.logger import logger

CHARTS_DIR = "static/trade_charts"
TICKERS = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "OP/USDT", "TON/USDT", "ARB/USDT",
    "MATIC/USDT", "SUI/USDT", "AVAX/USDT", "APT/USDT", "INJ/USDT", "LDO/USDT",
    "LINK/USDT", "RNDR/USDT", "TIA/USDT", "NEAR/USDT"
]
EXCHANGES = ["Binance", "Bybit", "OKX"]

# Целевые параметры
TARGET_DAILY_RANGE = (2.0, 5.0)  # 2-5% в день
MIN_VOLATILITY_PCT = 0.3
MAX_SINGLE_TRADE_PCT = 2.0  # максимум 2% за одну сделку
TARGET_WINRATE = 0.82  # 82% винрейт

_last_ticker = None

EXCHANGE_COLORS = {
    "Binance": "🟡",
    "Bybit": "🟠",
    "OKX": "⚫️",
}


def get_moscow_trading_day():
    """Возвращает начало и конец торгового дня по Москве (18:00-18:00)"""
    now = datetime.utcnow() + timedelta(hours=3)  # MSK

    if now.hour >= 18:
        # После 18:00 - считаем текущий торговый день
        start = datetime.combine(now.date(), dtime(18, 0)) - timedelta(hours=3)  # UTC
        end = start + timedelta(days=1)
    else:
        # До 18:00 - считаем предыдущий торговый день
        start = datetime.combine(now.date() - timedelta(days=1), dtime(18, 0)) - timedelta(hours=3)
        end = start + timedelta(days=1)

    return start, end, now


def calculate_daily_stats(db):
    """Считает статистику за текущий торговый день"""
    start, end, now = get_moscow_trading_day()

    # Общая доходность
    total_pct = db.query(func.sum(Trade.result_pct)).filter(
        Trade.created_at >= start,
        Trade.created_at < min(end, now)
    ).scalar() or 0.0

    # Количество сделок
    total_trades = db.query(Trade).filter(
        Trade.created_at >= start,
        Trade.created_at < min(end, now)
    ).count()

    # Прибыльные сделки
    profitable_trades = db.query(Trade).filter(
        Trade.created_at >= start,
        Trade.created_at < min(end, now),
        Trade.is_profitable == True
    ).count()

    winrate = profitable_trades / total_trades if total_trades > 0 else 0.0

    # Время до конца торгового дня
    time_left_seconds = (end - now).total_seconds()

    return {
        'total_pct': total_pct,
        'total_trades': total_trades,
        'winrate': winrate,
        'time_left_seconds': max(time_left_seconds, 0),
        'start': start,
        'end': end,
        'now': now
    }


def should_be_profitable(stats):
    """Определяет, должна ли следующая сделка быть прибыльной"""
    if stats['total_trades'] == 0:
        return True  # Первая сделка прибыльная

    current_winrate = stats['winrate']

    if current_winrate < TARGET_WINRATE - 0.05:  # Слишком низкий винрейт
        return True
    elif current_winrate > TARGET_WINRATE + 0.05:  # Слишком высокий винрейт
        return random.random() < 0.3  # 30% шанс прибыльной
    else:
        return random.random() < 0.85  # 85% шанс прибыльной (немного выше цели)


def calculate_target_pct(stats):
    """Рассчитывает целевой процент для следующей сделки"""
    current_pct = stats['total_pct']
    time_left_hours = stats['time_left_seconds'] / 3600

    # Если времени мало (меньше 2 часов), не генерируем сделки
    if time_left_hours < 2:
        return None

    # Среднее количество сделок в день: 20-35
    estimated_trades_left = max(1, int(time_left_hours * 1.5))  # ~1.5 сделки в час

    if current_pct < TARGET_DAILY_RANGE[0]:
        # Нужно добавить доходности
        needed = TARGET_DAILY_RANGE[0] + random.uniform(0, 1.5) - current_pct
        target = needed / estimated_trades_left
        return min(target, MAX_SINGLE_TRADE_PCT)
    elif current_pct > TARGET_DAILY_RANGE[1]:
        # Слишком много, нужно умерить
        excess = current_pct - TARGET_DAILY_RANGE[1]
        target = -excess / estimated_trades_left
        return max(target, -MAX_SINGLE_TRADE_PCT)
    else:
        # В пределах нормы, небольшие колебания
        return random.uniform(-0.5, 0.8)


def draw_candlestick_chart(candles, entry_idx, exit_idx, trade_id, direction):
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import pandas as pd

    df = pd.DataFrame(candles)
    df.index = pd.DatetimeIndex(df["time"])
    df = df[["open", "high", "low", "close"]].astype(float)

    entry_price = df.iloc[entry_idx]["close"]
    exit_price = df.iloc[exit_idx]["close"]
    entry_time = df.index[entry_idx]
    exit_time = df.index[exit_idx]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df.index, df["close"], color="lightblue", linewidth=1.5)

    ax.axhline(entry_price, linestyle="--", color="lime", linewidth=1, alpha=0.7)
    ax.axhline(exit_price, linestyle="--", color="red", linewidth=1, alpha=0.7)

    ax.plot(entry_time, entry_price, marker='o', color='lime', markersize=8)
    ax.plot(exit_time, exit_price, marker='o', color='red', markersize=8)

    ax.set_title(f"Tradient AI Trade — {direction}", fontsize=14, weight='bold', color='white', pad=15)
    ax.set_ylabel("Цена (USDT)", color='white')
    ax.grid(True, linestyle="--", alpha=0.3)

    ax.tick_params(colors='gray')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.xticks(rotation=45)

    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')

    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, f"{trade_id}.png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.savefig(path, dpi=200)
    plt.close()
    return path


def find_suitable_trade(target_pct, should_profit):
    """Ищет подходящую сделку с нужными параметрами"""
    global _last_ticker

    for attempt in range(50):  # Увеличиваем количество попыток
        # Выбираем тикер (не повторяем предыдущий)
        tickers_pool = [t for t in TICKERS if t != _last_ticker]
        ticker = random.choice(tickers_pool) if tickers_pool else random.choice(TICKERS)

        exchange = random.choice(EXCHANGES)
        symbol = ticker.replace("/", "")

        try:
            candles = get_candles(symbol=symbol, interval="15m", limit=96)
        except Exception as e:
            logger.warning(f"Ошибка получения данных для {ticker}: {e}")
            continue

        if len(candles) < 50:
            continue

        # Случайные точки входа и выхода
        entry_idx = random.randint(5, len(candles) - 20)
        exit_idx = entry_idx + random.randint(3, min(25, len(candles) - entry_idx - 1))

        entry = candles[entry_idx]
        exit = candles[exit_idx]

        for direction in ["LONG", "SHORT"]:
            # Рассчитываем результат
            if direction == "LONG":
                pct = ((exit["close"] - entry["close"]) / entry["close"]) * 100
            else:
                pct = ((entry["close"] - exit["close"]) / entry["close"]) * 100

            is_profitable = pct > 0

            # Проверяем соответствие критериям
            if abs(pct) < MIN_VOLATILITY_PCT:
                continue

            if abs(pct) > MAX_SINGLE_TRADE_PCT:
                continue

            if should_profit != is_profitable:
                continue

            # Проверяем близость к целевому проценту
            if target_pct is not None:
                diff = abs(pct - target_pct)
                if diff > 1.0:  # Допуск ±1%
                    continue

            _last_ticker = ticker
            return {
                'ticker': ticker,
                'exchange': exchange,
                'direction': direction,
                'entry_idx': entry_idx,
                'exit_idx': exit_idx,
                'entry_price': entry["close"],
                'exit_price': exit["close"],
                'result_pct': round(pct, 2),
                'result_usd': round(pct / 100 * 500, 2),
                'entry_time': entry["time"],
                'exit_time': exit["time"],
                'is_profitable': is_profitable,
                'candles': candles
            }

    return None


def generate_fake_trade():
    """Основная функция генерации трейда"""
    db = SessionLocal()
    try:
        # Получаем статистику текущего дня
        stats = calculate_daily_stats(db)

        logger.info(
            f"[TRADE] 📊 День: {stats['total_pct']:.2f}%, сделок: {stats['total_trades']}, винрейт: {stats['winrate']:.1%}")

        # Определяем параметры следующей сделки
        should_profit = should_be_profitable(stats)
        target_pct = calculate_target_pct(stats)

        if target_pct is None:
            logger.info("[TRADE] ⏰ Слишком мало времени до конца дня, пропускаем")
            return None

        logger.info(f"[TRADE] 🎯 Цель: {target_pct:.2f}%, прибыль: {should_profit}")

        # Ищем подходящую сделку
        trade_data = find_suitable_trade(target_pct, should_profit)

        if not trade_data:
            logger.warning("[TRADE] ❌ Не удалось найти подходящую сделку")
            return None

        # Создаем запись в БД
        trade = Trade(
            ticker=trade_data['ticker'],
            exchange=trade_data['exchange'],
            direction=trade_data['direction'],
            entry_price=trade_data['entry_price'],
            exit_price=trade_data['exit_price'],
            result_pct=trade_data['result_pct'],
            result_usd=trade_data['result_usd'],
            entry_time=trade_data['entry_time'],
            exit_time=trade_data['exit_time'],
            is_profitable=trade_data['is_profitable'],
        )

        db.add(trade)
        db.commit()
        db.refresh(trade)

        # Генерируем график
        try:
            chart_path = draw_candlestick_chart(
                trade_data['candles'],
                trade_data['entry_idx'],
                trade_data['exit_idx'],
                trade.id,
                trade_data['direction']
            )
            trade.chart_path = chart_path
            db.commit()
        except Exception as e:
            logger.error(f"[TRADE] ❌ Ошибка создания графика: {e}")

        # Обновляем статистику
        new_total = stats['total_pct'] + trade_data['result_pct']
        logger.success(
            f"[TRADE] ✅ ID={trade.id} | {trade_data['ticker']} | {trade_data['direction']} | "
            f"{trade_data['result_pct']:.2f}% | День: {new_total:.2f}%"
        )

        return trade.id

    except Exception as e:
        logger.error(f"[TRADE] ❌ Ошибка генерации: {e}")
        db.rollback()
        return None
    finally:
        db.close()