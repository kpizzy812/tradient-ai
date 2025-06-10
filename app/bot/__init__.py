from aiogram import Dispatcher
from .handlers import start_router, deposit_router, withdraw_router, admin_router, reinvest_router

def register_handlers(dp: Dispatcher):
    dp.include_router(start_router)
    dp.include_router(deposit_router)
    dp.include_router(withdraw_router)
    dp.include_router(admin_router)
    dp.include_router(reinvest_router)
