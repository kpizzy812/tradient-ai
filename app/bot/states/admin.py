# app/bot/states/admin.py
from aiogram.fsm.state import StatesGroup, State


class AdminStates(StatesGroup):
    # Основные состояния
    menu = State()
    user_input_id = State()
    user_detail = State()
    editing_referrer = State()
    editing_balance = State()
    editing_pool = State()
    choosing_ref_level = State()
    editing_pool_amount = State()

    # Статистика
    stats_menu = State()
    stats_general = State()
    stats_finance = State()  # Добавляем состояние финансов
    stats_deposits = State()
    stats_withdrawals = State()
    stats_users = State()
    stats_pools = State()
    stats_period = State()

    # Управление заявками
    deposits_filter = State()
    deposits_list = State()
    withdraws_filter = State()
    withdraws_list = State()

    # Управление системой
    management_menu = State()
    editing_addresses = State()
    editing_pools = State()
    editing_fees = State()
    editing_referral = State()
    editing_coefficients = State()
    system_management = State()

    # Рассылка
    broadcast_menu = State()
    broadcast_pool_selection = State()
    broadcast_amount_input = State()
    broadcast_date_input = State()
    broadcast_custom_input = State()
    broadcast_message_input = State()