from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Awaitable, Dict, Any
from app.core.logger import logger


class MessageLoggerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        logger.info(f"[{event.from_user.id}] {event.text}")
        return await handler(event, data)
