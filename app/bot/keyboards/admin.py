# app/bot/keyboards/admin.py
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def get_admin_menu_kb() -> InlineKeyboardMarkup:
    """
    Главное меню для админа:
    Пользователи / Статистика / Пополнения / Выводы / Рассылка
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👤 Пользователи", callback_data="admin_users"),
                InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
            ],
            [
                InlineKeyboardButton(text="📈 Пополнения", callback_data="admin_deposits"),
                InlineKeyboardButton(text="📉 Выводы", callback_data="admin_withdraws")
            ],
            [
                InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast"),
                InlineKeyboardButton(text="⚙️ Управление", callback_data="admin_management")
            ]
        ]
    )

def get_stats_menu_kb() -> InlineKeyboardMarkup:
    """Меню статистики"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Общая", callback_data="stats_general"),
                InlineKeyboardButton(text="💰 Финансы", callback_data="stats_finance"),
            ],
            [
                InlineKeyboardButton(text="📈 Пополнения", callback_data="stats_deposits"),
                InlineKeyboardButton(text="📉 Выводы", callback_data="stats_withdrawals"),
            ],
            [
                InlineKeyboardButton(text="👥 Пользователи", callback_data="stats_users"),
                InlineKeyboardButton(text="🏦 Пулы", callback_data="stats_pools"),
            ],
            [
                InlineKeyboardButton(text="📅 За период", callback_data="stats_period"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu"),
            ]
        ]
    )

def get_back_to_stats_kb() -> InlineKeyboardMarkup:
    """Кнопка возврата к статистике"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Обновить", callback_data="stats_refresh"),
                InlineKeyboardButton(text="🔙 К статистике", callback_data="admin_stats")
            ]
        ]
    )

def get_back_to_menu_kb() -> InlineKeyboardMarkup:
    """Кнопка возврата в главное меню"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 В главное меню", callback_data="admin_menu")]
        ]
    )