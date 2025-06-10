from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def get_admin_menu_kb() -> InlineKeyboardMarkup:
    """
    Главное меню для админа:
    Пользователи / Пополнения / Выводы / Рассылка
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Пользователи", callback_data="admin_users")],
            [InlineKeyboardButton(text="Пополнения",   callback_data="admin_deposits")],
            [InlineKeyboardButton(text="Выводы",       callback_data="admin_withdraws")],
            [InlineKeyboardButton(text="Рассылка",     callback_data="admin_broadcast")],
        ]
    )
