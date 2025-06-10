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

EXCHANGE_COLORS = {
    "Binance": "🟡",
    "Bybit": "🟠",
    "OKX": "⚫️",
}

MIN_VOLATILITY_PCT = 0.3   # минимальный % сделки
_last_ticker = None

def calculate_winrate(db):
    total = db.query(Trade).count()
    profitable = db.query(Trade).filter(Trade.is_profitable == True).count()
    if total == 0:
        return 0.0
    return profitable / total

def decide_profit(winrate):
    """
    Когда дневная доходность уже в [2%, 5%],
    решаем, делать ли прибыльную сделку, ориентируясь на винрейт.
    """
    if winrate < 0.85:
        return random.random() < 0.95
    elif winrate > 0.85:
        return random.random() < 0.25
    return random.random() < 0.80

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

def generate_fake_trade():
    """
    Адаптированная функция: публикация в Telegram идёт с
    «случайной» задержкой 20–50 мин, поэтому здесь мы
    расчёты строим не на «слоты», а на фактическое время до полуночи.
    """
    global _last_ticker

    # 1) Берём текущее время (UTC+3), началом суток считаем 00:00 (UTC+3)
    now = datetime.utcnow() + timedelta(hours=3)
    today = now.date()
    start_of_day = datetime.combine(today, dtime.min)
    end_of_day = datetime.combine(today + timedelta(days=1), dtime.min)

    logger.info(f"[FAKE_TRADE] ▶️ Запущена генерация трейда на {now.isoformat()}")

    db = SessionLocal()
    try:
        # --------------------------------------------
        # 2) Считаем текущую дневную доходность (в %)
        # --------------------------------------------
        current_day_profit = db.query(
            func.coalesce(func.sum(Trade.result_pct), 0.0)
        ).filter(Trade.created_at >= start_of_day, Trade.created_at <= now).scalar() or 0.0
        logger.info(f"[FAKE_TRADE] 📊 Текущая дневная доходность: {current_day_profit:.2f}%")

        # --------------------------------------------
        # 3) Считаем, сколько секунд осталось до полуночи
        # --------------------------------------------
        seconds_until_end = (end_of_day - now).total_seconds()
        if seconds_until_end < 1:
            seconds_until_end = 1  # чтобы не делить на ноль

        # --------------------------------------------
        # 4) Вычисляем, насколько «нам не хватает» до 2% и на сколько мы «перебрали» 5%
        # --------------------------------------------
        needed_to_min = 2.0 - current_day_profit   # >0 => надо «добавить» до 2%
        needed_to_max = 5.0 - current_day_profit   # <0 => мы уже за 5%

        # --------------------------------------------
        # 5) Рассчитываем «средний % в секунду»:
        #    - Если current < 2  ⇒ нам нужно avg_up_per_sec = needed_to_min / seconds_until_end  (>0)
        #    - Если current > 5  ⇒ avg_down_per_sec = needed_to_max / seconds_until_end (<0)
        #    - Если 2 ≤ current ≤ 5 ⇒ avg_target_per_sec как можно ближе к 0,
        #         но чуть «подпираем» границы (возьмём какой-нибудь avg ±, чтобы ограничивать «слишком жирные» сделки).
        # --------------------------------------------
        if current_day_profit < 2.0:
            mode = "FORCE_PROFIT"
            avg_target_per_sec = needed_to_min / seconds_until_end  # > 0
        elif current_day_profit > 5.0:
            mode = "FORCE_LOSS"
            avg_target_per_sec = needed_to_max / seconds_until_end  # < 0
        else:
            mode = "RANDOM_BALANCE"
            # Если мы в диапазоне [2, 5], то avg_target_per_sec можно считать очень малым числом,
            # но всё же выступить «буфером» при отсеивании «слишком жирных» сделок:
            # возьмём min(|needed_to_min|, |needed_to_max|) / seconds_until_end:
            base = needed_to_min if needed_to_min > 0 else needed_to_max  # base может быть + или −, близко к 0
            avg_target_per_sec = base / seconds_until_end

        logger.info(
            f"[FAKE_TRADE] 🔄 Режим: {mode}, "
            f"avg_target_per_sec ≈ {avg_target_per_sec:.8f} (секунд до конца дня: {seconds_until_end:.0f})"
        )

        # --------------------------------------------
        # 6) Сколько секунд пройдёт до следующей публикации?
        #    Тут мы его ещё не знаем (delay определится после создания trade),
        #    поэтому поступаем так: для «FORCE» режимов мы знаем avg_target_per_sec,
        #    и можем «целиться» примерно в avg_target_pct = avg_target_per_sec *
        #    typical_delay_secs. Предположим, typical_delay = 30 мин = 1800 сек
        #    (это среднее между 20 и 50).
        #    Для точности потом проверим итоговый result_pct ± tolerance.
        # --------------------------------------------
        typical_delay_secs = 30 * 60  # 30 минут в секундах
        avg_target_pct = avg_target_per_sec * typical_delay_secs
        # Если режим RANDOM_BALANCE, avg_target_pct может быть очень малым (−0.001…+0.001 и т. п.)

        # --------------------------------------------
        # 7) Теперь попытаемся за 20 итераций «подогнать» pct ≈ avg_target_pct,
        #    с учётом:
        #      - Для FORCE_PROFIT ⇒ is_profit=True
        #      - Для FORCE_LOSS   ⇒ is_profit=False
        #      - Для RANDOM_BALANCE ⇒ решаем по vinrate и не даём «прыгнуть» ниже 0% и выше 7%
        #      - Абсолютная «жирность» сделки (отсекание очень больших отклонений)
        # --------------------------------------------
        for _ in range(20):
            tickers_pool = [t for t in TICKERS if t != _last_ticker]
            ticker = random.choice(tickers_pool) if tickers_pool else random.choice(TICKERS)
            _last_ticker = ticker

            exchange = random.choice(EXCHANGES)
            symbol = ticker.replace("/", "")
            candles = get_candles(symbol=symbol, interval="15m", limit=96)  # 96 свечей = 24 ч

            if len(candles) < 96:
                logger.info(f"❌ Пропущен {ticker} — недостаточно свечей ({len(candles)})")
                continue

            entry_idx = random.randint(5, len(candles) - 10)
            max_exit_range = min(30, len(candles) - entry_idx - 1)
            exit_idx = entry_idx + random.randint(5, max_exit_range)
            entry = candles[entry_idx]
            exit = candles[exit_idx]

            for direction in ["LONG", "SHORT"]:
                # Вычисляем будет ли profit
                is_profit = (exit["close"] > entry["close"]) if direction == "LONG" else (exit["close"] < entry["close"])
                pct = ((exit["close"] - entry["close"]) / entry["close"]) * 100
                if direction == "SHORT":
                    pct *= -1

                # Фильтруем «мелкую» волатильность
                if abs(pct) < MIN_VOLATILITY_PCT:
                    continue

                # -------------------------
                # FORCE_PROFIT: только + сделки,
                # и не слишком большой процент (не более 3× avg_target_pct)
                # -------------------------
                if mode == "FORCE_PROFIT":
                    if not is_profit:
                        continue
                    # Если avg_target_pct слишком мал (например, 0.03%), чтобы не сгенерить +5%,
                    # добавим барьер: max_allowed = max(abs(avg_target_pct)*3, MIN_VOLATILITY_PCT)
                    max_allowed = max(abs(avg_target_pct) * 3, MIN_VOLATILITY_PCT)
                    if pct > max_allowed:
                        continue

                # -------------------------
                # FORCE_LOSS: только − сделки,
                # и не слишком «жирный» убыток (не более 3× |avg_target_pct|)
                # -------------------------
                elif mode == "FORCE_LOSS":
                    if is_profit:
                        continue
                    max_allowed_loss = min(-abs(avg_target_pct) * 3, -MIN_VOLATILITY_PCT)
                    # pct меньше, чем max_allowed_loss (больший по модулю отрицательный) ⇒ пропускаем
                    if pct < max_allowed_loss:
                        continue

                # -------------------------
                # RANDOM_BALANCE:
                # решаем по винрейту, чтобы был profit/loss,
                # но не выводим итог за 0% и 7%,
                # и не допускаем «чрезмерных» сделок (>|3× avg_target_pct|)
                # -------------------------
                else:
                    winrate = calculate_winrate(db)
                    want_profit = decide_profit(winrate)
                    if want_profit != is_profit:
                        continue

                    hypothetical = current_day_profit + pct
                    # Если после сделки уйдём ниже 0% или выше 7% ⇒ пропускаем
                    if hypothetical < 0.0 or hypothetical > 7.0:
                        continue

                    # Ограничим «жирность» сделки:
                    threshold = max(abs(avg_target_pct) * 3, MIN_VOLATILITY_PCT)
                    if abs(pct) > threshold:
                        continue

                # Если до этого момента всё ок — фиксируем trade
                trade = Trade(
                    ticker=ticker,
                    exchange=exchange,
                    direction=direction,
                    entry_price=entry["close"],
                    exit_price=exit["close"],
                    result_pct=round(pct, 2),
                    result_usd=round(pct / 100 * 500, 2),
                    entry_time=entry["time"],
                    exit_time=exit["time"],
                    is_profitable=(pct > 0),
                )
                try:
                    db.add(trade)
                    db.commit()
                    db.refresh(trade)
                except Exception as e:
                    logger.error(f"[TRADE] ❌ Ошибка при коммите трейда: {e}")
                    db.rollback()
                    continue

                # Обновляем текущую дневную доходность
                current_day_profit += pct
                logger.success(
                    f"[TRADE] 🟢 ID={trade.id} | {ticker} | {direction} | {pct:.2f}% | "
                    f"mode={mode} | now_day_profit={current_day_profit:.2f}%"
                )

                # Генерируем и сохраняем график
                path = draw_candlestick_chart(candles, entry_idx, exit_idx, trade.id, direction)
                try:
                    trade.chart_path = path
                    db.commit()
                except Exception as e:
                    logger.error(f"[TRADE] ❌ Ошибка при сохранении chart_path: {e}")
                    db.rollback()

                return trade.id

        # Если за 20 попыток ничего не подошло, вернём None
        logger.warning("[TRADE] ❌ Не удалось подобрать сделку за 20 итераций.")
        return None

    finally:
        db.close()
