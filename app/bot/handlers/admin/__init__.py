from aiogram import Router

from .entry import router as entry_router
from .user import router as user_router
from .edit import router as edit_router
from .partners import router as partners_router
from .ban import router as ban_router
from .trade_commands import router as trade_commands_router
from .stats import router as stats_router

admin_router = Router()
admin_router.include_router(entry_router)
admin_router.include_router(user_router)
admin_router.include_router(edit_router)
admin_router.include_router(partners_router)
admin_router.include_router(ban_router)
admin_router.include_router(stats_router)

admin_router.include_router(trade_commands_router)  # НОВОЕ