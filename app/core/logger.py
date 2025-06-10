from loguru import logger
from pathlib import Path
import sys

LOGS_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logger.remove()

logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <cyan>{message}</cyan>"
)

# 🔹 Лог API
logger.add(
    LOGS_DIR / "api.log",
    level="INFO",
    rotation="1 day",
    retention="7 days",
    compression="zip",
    filter=lambda r: r["extra"].get("name") == "api"
)

# 🔸 Лог бота
logger.add(
    LOGS_DIR / "bot.log",
    level="INFO",
    rotation="1 day",
    retention="7 days",
    compression="zip",
    filter=lambda r: r["extra"].get("name") == "bot"
)
