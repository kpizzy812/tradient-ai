# app/bot/handlers/admin/__init__.py
from aiogram import Router

from .entry import router as entry_router
from .stats import router as stats_router  
from .user import router as user_router
from .edit import router as edit_router
from .deposits import router as deposits_router
from .withdrawals import router as withdrawals_router
from .management import router as management_router
from .broadcast import router as broadcast_router

# Создаем главный роутер для админки
admin_router = Router()

# Регистрируем все подроутеры
admin_router.include_router(entry_router)
admin_router.include_router(stats_router)
admin_router.include_router(user_router)
admin_router.include_router(edit_router)
admin_router.include_router(deposits_router)
admin_router.include_router(withdrawals_router)
admin_router.include_router(management_router)
admin_router.include_router(broadcast_router)

__all__ = ["admin_router"]