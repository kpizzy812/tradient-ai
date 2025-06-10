from aiogram.fsm.state import StatesGroup, State

class AdminStates(StatesGroup):
    menu = State()
    user_input_id = State()
    user_detail = State()
    editing_referrer = State()
    editing_balance = State()
    editing_pool = State()
    choosing_ref_level = State()
    editing_pool_amount = State()
