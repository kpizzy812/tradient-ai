from .start import router as start_router
from .deposit import router as deposit_router
from .withdraw import router as withdraw_router
from app.bot.handlers.admin import admin_router
from .reinvest import router as reinvest_router

__all__ = [
    "start_router",
    "deposit_router",
    "withdraw_router",
    "admin_router",
    "reinvest_router",
]
