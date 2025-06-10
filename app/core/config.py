from pydantic_settings import BaseSettings
from datetime import time
from typing import ClassVar, Optional
import os


class Settings(BaseSettings):
    # Основные параметры
    BOT_TOKEN: str = "8024565295:AAGmWeXeWmK3xD8xBu0e9dFss_iMFb7fUXk"
    BOT_USERNAME: str = "TradientBot"
    SUPPORT_URL: ClassVar[str] = "https://t.me/tradient_support"
    PROJECT_CHAT_ID: ClassVar[int] = -1002660218997
    TRADE_TOPIC_ID: ClassVar[int] = 2 # топик сделок
    DAILY_YIELD_TOPIC_ID: ClassVar[Optional[int]] = None
    DATABASE_URL: str = "sqlite:///./db.sqlite"
    CUTOFF_TIME: time = time(17, 30)
    YIELD_TIME_UTC_HOUR: int = 15  # 18:00 МСК
    MIN_WITHDRAW_USD: float = 5.0

    PAYMENT_ADDRESSES: ClassVar[dict[str, str]] = {
        "usdt_ton": "UQBbezryJkNY7rF7Al55p3StMb2iIS006-xr4Jwmh4eq7Hzb",
        "usdt_bep20": "UQBbezryJkNY7rF7Al55p3StMb2iIS006-xr4Jwmh4eq7Hzb",
        "card_ru": "5469 3800 1234 5678",
        "trx": "TToQQgkb5v6MQgfCdRy1iJ8uEPJReFazct"
    }

    # Доходность по коэффициентам
    POOL_YIELD_RANGES: ClassVar[dict[str, tuple[float, float]]] = {
        "Basic": (1.8, 2.2),
        "Smart": (2.4, 2.9),
        "Pro": (2.9, 3.4),
        "Alpha": (3.5, 4.2),
    }

    # Множитель доходности для каждого пула (1.0 = без изменений)
    POOL_COEFFICIENTS: dict[str, float] = {
        "Basic": 1.0,
        "Smart": 1.0,
        "Pro": 1.0,
        "Alpha": 1.0,
    }

    POOL_LIMITS: ClassVar[dict[str, dict[str, int]]] = {
        "Basic": {
            "min": 20,
            "max": 100,
            "max_per_user": 1000
        },
        "Smart": {
            "min": 100,
            "max": 250,
            "max_per_user": 2000
        },
        "Pro": {
            "min": 250,
            "max": 1000,
            "max_per_user": 4000
        },
        "Alpha": {
            "min": 1000,
            "max": 10000,
            "max_per_user": 8000
        }
    }

    # Комиссии на вывод по времени
    WITHDRAW_TIERS: ClassVar[dict[int, float]] = {
        0: 0.15,
        3: 0.10,
        7: 0.05,
        14: 0.00,
    }

    # Экспресс-режим
    WITHDRAW_EXPRESS_FEE: ClassVar[float] = 0.10  # 10%
    WITHDRAW_BASE_DAYS: ClassVar[int] = 5         # до скольки дней исполняется базовый вывод

    # Реферальная система
    REFERRAL_LEVELS: ClassVar[list[float]] = [10.0, 5.0, 3.0, 2.0, 1.0]

    # Языки и локаль
    SUPPORTED_LANGUAGES: ClassVar[list[str]] = ["ru", "en", "uk"]
    DEFAULT_LANGUAGE: ClassVar[str] = "ru"

    # Админы
    ADMIN_TG_IDS: ClassVar[list[int]] = [6084633525]

    # — новый блок для JWT —
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-very-secret-key")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_SECONDS: int = 60 * 60 * 24  # 1 сутки





settings = Settings()
