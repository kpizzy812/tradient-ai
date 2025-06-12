# app/services/smart_trade_generator.py - НОВЫЙ ФАЙЛ
import random
import os
from datetime import datetime, timedelta, time as dtime
from sqlalchemy import func
from app.core.utils.binance import get_candles
from app.models.trades import Trade
from app.core.db import SessionLocal
from app.core.logger import logger
from app.core.config import settings
import pytz

msk = pytz.timezone("Europe/Moscow")

CHARTS_DIR = "static/trade_charts"
TICKERS = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "OP/USDT", "TON/USDT", "ARB/USDT",
    "MATIC/USDT", "SUI/USDT", "AVAX/USDT", "APT/USDT", "INJ/USDT", "LDO/USDT",
    "LINK/USDT", "RNDR/USDT", "TIA/USDT", "NEAR/USDT"
]
EXCHANGES = ["Binance", "Bybit", "OKX"]

_last_ticker = None

EXCHANGE_COLORS = {
    "Binance": "🟡",
    "Bybit": "🟠",
    "OKX": "⚫️",
}

def get_trading_day_bounds():
    """Возвращает границы текущего торгового дня (18:00-18:00 МСК)"""
    now_utc = datetime.utcnow()

    # Время финализации в UTC
    finalize_hour_utc = settings.YIELD_TIME_UTC_HOUR

    # Определяем границы торгового дня
    if now_utc.hour >= finalize_hour_utc:
        # После времени финализации - текущий торговый день
        start_utc = datetime.combine(now_utc.date(), dtime(finalize_hour_utc, 0))
        end_utc = start_utc + timedelta(days=1)
    else:
        # До времени финализации - предыдущий торговый день
        start_utc = datetime.combine(now_utc.date() - timedelta(days=1), dtime(finalize_hour_utc, 0))
        end_utc = datetime.combine(now_utc.date(), dtime(finalize_hour_utc, 0))

    return start_utc, end_utc, now_utc


def get_current_day_stats():
    """Получает статистику текущего торгового дня"""
    db = SessionLocal()
    try:
        start_utc, end_utc, now_utc = get_trading_day_bounds()

        # Текущая доходность
        current_yield = db.query(func.sum(Trade.result_pct)).filter(
            Trade.created_at >= start_utc,
            Trade.created_at < min(end_utc, now_utc)
        ).scalar() or 0.0

        # Количество трейдов
        trades_count = db.query(Trade).filter(
            Trade.created_at >= start_utc,
            Trade.created_at < min(end_utc, now_utc)
        ).count()

        # Время до финализации
        hours_left = (end_utc - now_utc).total_seconds() / 3600

        return {
            'current_yield': round(current_yield, 2),
            'trades_count': trades_count,
            'hours_left': max(hours_left, 0),
            'start_utc': start_utc,
            'end_utc': end_utc,
            'is_active': hours_left > 0
        }
    finally:
        db.close()


def calculate_target_yield(stats):
    """Рассчитывает целевую доходность для следующего трейда"""
    current_yield = stats['current_yield']
    hours_left = stats['hours_left']

    if hours_left <= 0:
        return None  # Торговый день закончен

    target_min, target_max = settings.DAILY_YIELD_RANGE
    target_center = (target_min + target_max) / 2

    # Если уже в диапазоне и времени достаточно - небольшие колебания
    if target_min <= current_yield <= target_max and hours_left > 2:
        return random.uniform(-0.3, 0.5)

    # Рассчитываем сколько нужно добавить/убрать
    if current_yield < target_min:
        # Недобираем
        needed = target_center - current_yield
        urgency = 1.0 if hours_left > 4 else 2.0  # Удваиваем если мало времени
        return min(needed * urgency / max(hours_left, 1), 2.0)  # Максимум 2% за трейд

    elif current_yield > target_max:
        # Перебираем
        excess = current_yield - target_center
        urgency = 1.0 if hours_left > 4 else 2.0
        return max(-excess * urgency / max(hours_left, 1), -2.0)  # Максимум -2% за трейд

    else:
        # В диапазоне - поддерживаем
        return random.uniform(-0.5, 0.5)


def calculate_next_trade_delay(stats):
    """Рассчитывает задержку до следующего трейда"""
    current_yield = stats['current_yield']
    hours_left = stats['hours_left']

    if hours_left <= 0:
        return None

    target_min, target_max = settings.DAILY_YIELD_RANGE
    base_min, base_max = settings.TRADE_FREQUENCY_MINUTES

    # Базовая задержка
    base_delay = random.randint(base_min, base_max)

    # Корректировки по ситуации
    if hours_left <= settings.CORRECTION_THRESHOLD_HOURS:
        # Критическое время - учащаем трейды
        if current_yield < target_min or current_yield > target_max:
            base_delay = random.randint(15, 30)  # Каждые 15-30 минут
        else:
            base_delay = random.randint(20, 45)  # Каждые 20-45 минут

    elif hours_left <= 4:
        # Подготовительное время
        if current_yield < target_min * 0.7 or current_yield > target_max * 1.3:
            base_delay = random.randint(20, 40)
        else:
            base_delay = random.randint(base_min, base_max)

    else:
        # Обычное время - стандартные интервалы
        base_delay = random.randint(base_min, base_max)

    return base_delay * 60  # Переводим в секунды


def find_suitable_trade(target_yield, retries=30):
    """Ищет подходящий трейд с нужной доходностью"""
    global _last_ticker

    for attempt in range(retries):
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

            # Проверяем подходит ли результат
            if abs(pct) < 0.2:  # Слишком маленький
                continue

            if abs(pct) > 3.0:  # Слишком большой
                continue

            # Проверяем близость к целевому значению
            if target_yield is not None:
                diff = abs(pct - target_yield)
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
                'is_profitable': pct > 0,
                'candles': candles
            }

    return None


def draw_candlestick_chart(candles, entry_idx, exit_idx, trade_id, direction):
    """Рисует график трейда"""
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


def generate_smart_trade():
    """Главная функция генерации умного трейда"""
    # Получаем статистику дня
    stats = get_current_day_stats()

    if not stats['is_active']:
        logger.info("[SMART_TRADE] Торговый день неактивен")
        return None

    # Рассчитываем целевую доходность
    target_yield = calculate_target_yield(stats)

    if target_yield is None:
        logger.info("[SMART_TRADE] Торговый день завершен")
        return None

    logger.info(
        f"[SMART_TRADE] Текущая доходность: {stats['current_yield']:.2f}%, "
        f"цель: {target_yield:.2f}%, времени: {stats['hours_left']:.1f}ч"
    )

    # Ищем подходящий трейд
    trade_data = find_suitable_trade(target_yield)

    if not trade_data:
        logger.warning("[SMART_TRADE] Не удалось найти подходящий трейд")
        return None

    # Сохраняем в БД
    db = SessionLocal()
    try:
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

        # Создаем график
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
            logger.error(f"[SMART_TRADE] Ошибка создания графика: {e}")

        # Новая статистика
        new_yield = stats['current_yield'] + trade_data['result_pct']
        target_min, target_max = settings.DAILY_YIELD_RANGE

        status = "✅" if target_min <= new_yield <= target_max else "⚠️"

        logger.success(
            f"[SMART_TRADE] {status} Трейд #{trade.id} | {trade_data['ticker']} | "
            f"{trade_data['direction']} | {trade_data['result_pct']:+.2f}% | "
            f"Итого: {new_yield:.2f}%"
        )

        return trade.id

    except Exception as e:
        logger.error(f"[SMART_TRADE] Ошибка сохранения трейда: {e}")
        db.rollback()
        return None
    finally:
        db.close()