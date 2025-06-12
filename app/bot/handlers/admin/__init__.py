# app/bot/handlers/admin/__init__.py
from aiogram import Router

from .entry import router as entry_router
from .user import router as user_router
from .edit import router as edit_router
from .partners import router as partners_router
from .ban import router as ban_router
from .yield_management import router as yield_management_router

admin_router = Router()
admin_router.include_router(entry_router)
admin_router.include_router(user_router)
admin_router.include_router(edit_router)
admin_router.include_router(partners_router)
admin_router.include_router(ban_router)
admin_router.include_router(yield_management_router)
