# app/bot/handlers/admin/management.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
import json
import os
from typing import Dict, Any

from app.core.config import settings
from app.bot.states.admin import AdminStates

router = Router()


def get_management_menu_kb():
    """Главное меню управления"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💳 Адреса кошельков", callback_data="manage_addresses"),
                InlineKeyboardButton(text="🏦 Настройки пулов", callback_data="manage_pools")
            ],
            [
                InlineKeyboardButton(text="💸 Комиссии вывода", callback_data="manage_fees"),
                InlineKeyboardButton(text="👥 Реферальная система", callback_data="manage_referral")
            ],
            [
                InlineKeyboardButton(text="📊 Коэффициенты доходности", callback_data="manage_coefficients"),
                InlineKeyboardButton(text="⚙️ Системные настройки", callback_data="manage_system")
            ],
            [
                InlineKeyboardButton(text="🔙 В главное меню", callback_data="admin_menu")
            ]
        ]
    )


def get_back_to_management_kb():
    """Кнопка возврата к управлению"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К управлению", callback_data="admin_management")]
        ]
    )


@router.callback_query(F.data == "admin_management")
async def show_management_menu(call: CallbackQuery, state: FSMContext):
    """Показать меню управления"""
    text = (
        "⚙️ <b>Управление системой</b>\n\n"
        "Выберите раздел для настройки:"
    )

    await call.message.edit_text(text, reply_markup=get_management_menu_kb())
    await state.set_state(AdminStates.management_menu)


@router.callback_query(StateFilter(AdminStates.management_menu), F.data == "manage_addresses")
async def show_payment_addresses(call: CallbackQuery, state: FSMContext):
    """Показать адреса для пополнения"""
    addresses = settings.PAYMENT_ADDRESSES

    text = "💳 <b>Адреса для пополнения</b>\n\n"

    for currency, address in addresses.items():
        currency_name = {
            "usdt_ton": "USDT (TON)",
            "usdt_bep20": "USDT (BEP20)",
            "card_ru": "Карта РФ",
            "trx": "TRX"
        }.get(currency, currency.upper())

        text += f"<b>{currency_name}:</b>\n<code>{address}</code>\n\n"

    text += "Введите команду для изменения:\n<code>/set_address [валюта] [новый_адрес]</code>\n\n"
    text += "Пример: <code>/set_address usdt_ton UQBnew...</code>"

    await call.message.edit_text(text, reply_markup=get_back_to_management_kb(), parse_mode="HTML")
    await state.set_state(AdminStates.editing_addresses)


@router.callback_query(StateFilter(AdminStates.management_menu), F.data == "manage_pools")
async def show_pool_settings(call: CallbackQuery, state: FSMContext):
    """Показать настройки пулов"""
    pools = settings.POOL_LIMITS
    yields = settings.POOL_YIELD_RANGES
    coefficients = settings.POOL_COEFFICIENTS

    text = "🏦 <b>Настройки пулов</b>\n\n"

    for pool_name, limits in pools.items():
        yield_range = yields.get(pool_name, (0, 0))
        coeff = coefficients.get(pool_name, 1.0)

        text += (
            f"<b>{pool_name}:</b>\n"
            f"• Лимиты: ${limits['min']} - ${limits['max']} (макс. на юзера: ${limits['max_per_user']})\n"
            f"• Доходность: {yield_range[0]:.1f}% - {yield_range[1]:.1f}%\n"
            f"• Коэффициент: {coeff:.2f}\n\n"
        )

    text += (
        "Команды для изменения:\n"
        "<code>/set_pool_limits [пул] [мин] [макс] [макс_на_юзера]</code>\n"
        "<code>/set_pool_yield [пул] [мин%] [макс%]</code>\n"
        "<code>/set_pool_coeff [пул] [коэффициент]</code>\n\n"
        "Пример: <code>/set_pool_limits Basic 25 150 1200</code>"
    )

    await call.message.edit_text(text, reply_markup=get_back_to_management_kb(), parse_mode="HTML")
    await state.set_state(AdminStates.editing_pools)


@router.callback_query(StateFilter(AdminStates.management_menu), F.data == "manage_fees")
async def show_withdraw_fees(call: CallbackQuery, state: FSMContext):
    """Показать комиссии за вывод"""
    tiers = settings.WITHDRAW_TIERS
    express_fee = settings.WITHDRAW_EXPRESS_FEE
    base_days = settings.WITHDRAW_BASE_DAYS

    text = "💸 <b>Комиссии за вывод</b>\n\n"

    text += "<b>Базовый режим (по времени после депозита):</b>\n"
    for days, fee in sorted(tiers.items()):
        if days == 0:
            text += f"• Сразу: {fee * 100:.1f}%\n"
        else:
            text += f"• Через {days} дн.: {fee * 100:.1f}%\n"

    text += f"\n<b>Экспресс-режим:</b> {express_fee * 100:.1f}%\n"
    text += f"<b>Срок базового вывода:</b> до {base_days} дней\n\n"

    text += (
        "Команды для изменения:\n"
        "<code>/set_withdraw_tier [дни] [комиссия]</code>\n"
        "<code>/set_express_fee [комиссия]</code>\n"
        "<code>/set_base_days [дни]</code>\n\n"
        "Пример: <code>/set_withdraw_tier 7 0.03</code> (3%)"
    )

    await call.message.edit_text(text, reply_markup=get_back_to_management_kb(), parse_mode="HTML")
    await state.set_state(AdminStates.editing_fees)


@router.callback_query(StateFilter(AdminStates.management_menu), F.data == "manage_referral")
async def show_referral_settings(call: CallbackQuery, state: FSMContext):
    """Показать настройки реферальной системы"""
    levels = settings.REFERRAL_LEVELS

    text = "👥 <b>Реферальная система</b>\n\n"

    for i, percent in enumerate(levels, 1):
        text += f"• {i} уровень: {percent:.1f}%\n"

    text += (
        f"\nВсего уровней: {len(levels)}\n\n"
        "Команда для изменения:\n"
        "<code>/set_referral [уровень] [процент]</code>\n\n"
        "Пример: <code>/set_referral 1 12.0</code>"
    )

    await call.message.edit_text(text, reply_markup=get_back_to_management_kb(), parse_mode="HTML")
    await state.set_state(AdminStates.editing_referral)


@router.callback_query(StateFilter(AdminStates.management_menu), F.data == "manage_coefficients")
async def show_coefficients(call: CallbackQuery, state: FSMContext):
    """Показать коэффициенты доходности"""
    coefficients = settings.POOL_COEFFICIENTS

    text = "📊 <b>Коэффициенты доходности</b>\n\n"
    text += "Множители для расчета доходности по пулам:\n\n"

    for pool_name, coeff in coefficients.items():
        status = "🟢 Норма" if coeff == 1.0 else ("🔴 Снижен" if coeff < 1.0 else "🟡 Повышен")
        text += f"<b>{pool_name}:</b> {coeff:.2f} ({status})\n"

    text += (
        "\n<b>Как работает:</b>\n"
        "• 1.0 = обычная доходность\n"
        "• 0.8 = доходность снижена на 20%\n"
        "• 1.2 = доходность повышена на 20%\n\n"
        "Команда: <code>/set_coeff [пул] [коэффициент]</code>\n"
        "Пример: <code>/set_coeff Alpha 1.1</code>"
    )

    await call.message.edit_text(text, reply_markup=get_back_to_management_kb(), parse_mode="HTML")
    await state.set_state(AdminStates.editing_coefficients)


@router.callback_query(StateFilter(AdminStates.management_menu), F.data == "manage_system")
async def show_system_settings(call: CallbackQuery, state: FSMContext):
    """Показать системные настройки"""
    text = (
        "⚙️ <b>Системные настройки</b>\n\n"
        f"🤖 <b>Админы:</b> {len(settings.ADMIN_TG_IDS)} чел.\n"
        f"🌍 <b>Поддерживаемые языки:</b> ru, en, uk\n"
        f"📊 <b>База данных:</b> SQLite\n"
        f"🔄 <b>Статус системы:</b> Активна\n\n"

        "Доступные команды:\n"
        "<code>/add_admin [tg_id]</code> - добавить админа\n"
        "<code>/remove_admin [tg_id]</code> - удалить админа\n"
        "<code>/system_status</code> - статус системы\n"
        "<code>/backup_db</code> - создать резервную копию БД\n"
        "<code>/clear_logs</code> - очистить логи"
    )

    await call.message.edit_text(text, reply_markup=get_back_to_management_kb(), parse_mode="HTML")
    await state.set_state(AdminStates.system_management)


# Обработчики команд изменения настроек

@router.message(StateFilter(AdminStates.editing_addresses), F.text.startswith("/set_address"))
async def set_payment_address(msg: Message, state: FSMContext):
    """Изменить адрес для пополнения"""
    try:
        parts = msg.text.split(None, 2)
        if len(parts) != 3:
            await msg.answer("❌ Неверный формат. Используйте: /set_address [валюта] [адрес]")
            return

        currency = parts[1].lower()
        new_address = parts[2]

        if currency not in settings.PAYMENT_ADDRESSES:
            await msg.answer(f"❌ Неизвестная валюта: {currency}")
            return

        # Обновляем настройку
        settings.PAYMENT_ADDRESSES[currency] = new_address

        await msg.answer(f"✅ Адрес для {currency.upper()} обновлен")
        await show_payment_addresses(msg, state)

    except Exception as e:
        await msg.answer(f"❌ Ошибка: {e}")


@router.message(StateFilter(AdminStates.editing_pools), F.text.startswith("/set_pool_limits"))
async def set_pool_limits(msg: Message, state: FSMContext):
    """Изменить лимиты пула"""
    try:
        parts = msg.text.split()
        if len(parts) != 5:
            await msg.answer("❌ Формат: /set_pool_limits [пул] [мин] [макс] [макс_на_юзера]")
            return

        pool_name = parts[1]
        min_val = int(parts[2])
        max_val = int(parts[3])
        max_per_user = int(parts[4])

        if pool_name not in settings.POOL_LIMITS:
            await msg.answer(f"❌ Неизвестный пул: {pool_name}")
            return

        settings.POOL_LIMITS[pool_name] = {
            "min": min_val,
            "max": max_val,
            "max_per_user": max_per_user
        }

        await msg.answer(f"✅ Лимиты пула {pool_name} обновлены")
        await show_pool_settings(msg, state)

    except ValueError:
        await msg.answer("❌ Все значения должны быть числами")
    except Exception as e:
        await msg.answer(f"❌ Ошибка: {e}")


@router.message(StateFilter(AdminStates.editing_pools), F.text.startswith("/set_pool_yield"))
async def set_pool_yield(msg: Message, state: FSMContext):
    """Изменить доходность пула"""
    try:
        parts = msg.text.split()
        if len(parts) != 4:
            await msg.answer("❌ Формат: /set_pool_yield [пул] [мин%] [макс%]")
            return

        pool_name = parts[1]
        min_yield = float(parts[2])
        max_yield = float(parts[3])

        if pool_name not in settings.POOL_YIELD_RANGES:
            await msg.answer(f"❌ Неизвестный пул: {pool_name}")
            return

        settings.POOL_YIELD_RANGES[pool_name] = (min_yield, max_yield)

        await msg.answer(f"✅ Доходность пула {pool_name} обновлена: {min_yield}% - {max_yield}%")
        await show_pool_settings(msg, state)

    except ValueError:
        await msg.answer("❌ Проценты должны быть числами")
    except Exception as e:
        await msg.answer(f"❌ Ошибка: {e}")


@router.message(StateFilter(AdminStates.editing_pools), F.text.startswith("/set_pool_coeff"))
async def set_pool_coefficient(msg: Message, state: FSMContext):
    """Изменить коэффициент пула"""
    try:
        parts = msg.text.split()
        if len(parts) != 3:
            await msg.answer("❌ Формат: /set_pool_coeff [пул] [коэффициент]")
            return

        pool_name = parts[1]
        coefficient = float(parts[2])

        if pool_name not in settings.POOL_COEFFICIENTS:
            await msg.answer(f"❌ Неизвестный пул: {pool_name}")
            return

        settings.POOL_COEFFICIENTS[pool_name] = coefficient

        await msg.answer(f"✅ Коэффициент пула {pool_name} установлен: {coefficient}")
        await show_pool_settings(msg, state)

    except ValueError:
        await msg.answer("❌ Коэффициент должен быть числом")
    except Exception as e:
        await msg.answer(f"❌ Ошибка: {e}")


@router.message(StateFilter(AdminStates.editing_fees), F.text.startswith("/set_withdraw_tier"))
async def set_withdraw_tier(msg: Message, state: FSMContext):
    """Изменить комиссию за вывод по времени"""
    try:
        parts = msg.text.split()
        if len(parts) != 3:
            await msg.answer("❌ Формат: /set_withdraw_tier [дни] [комиссия]")
            return

        days = int(parts[1])
        fee = float(parts[2])

        settings.WITHDRAW_TIERS[days] = fee

        await msg.answer(f"✅ Комиссия через {days} дней установлена: {fee * 100:.1f}%")
        await show_withdraw_fees(msg, state)

    except ValueError:
        await msg.answer("❌ Неверный формат чисел")
    except Exception as e:
        await msg.answer(f"❌ Ошибка: {e}")


@router.message(StateFilter(AdminStates.editing_fees), F.text.startswith("/set_express_fee"))
async def set_express_fee(msg: Message, state: FSMContext):
    """Изменить комиссию экспресс-режима"""
    try:
        parts = msg.text.split()
        if len(parts) != 2:
            await msg.answer("❌ Формат: /set_express_fee [комиссия]")
            return

        fee = float(parts[1])
        settings.WITHDRAW_EXPRESS_FEE = fee

        await msg.answer(f"✅ Комиссия экспресс-режима установлена: {fee * 100:.1f}%")
        await show_withdraw_fees(msg, state)

    except ValueError:
        await msg.answer("❌ Комиссия должна быть числом")
    except Exception as e:
        await msg.answer(f"❌ Ошибка: {e}")


@router.message(StateFilter(AdminStates.editing_referral), F.text.startswith("/set_referral"))
async def set_referral_level(msg: Message, state: FSMContext):
    """Изменить процент реферального уровня"""
    try:
        parts = msg.text.split()
        if len(parts) != 3:
            await msg.answer("❌ Формат: /set_referral [уровень] [процент]")
            return

        level = int(parts[1]) - 1  # Преобразуем в индекс массива
        percent = float(parts[2])

        if level < 0 or level >= len(settings.REFERRAL_LEVELS):
            await msg.answer(f"❌ Уровень должен быть от 1 до {len(settings.REFERRAL_LEVELS)}")
            return

        settings.REFERRAL_LEVELS[level] = percent

        await msg.answer(f"✅ Процент {level + 1} уровня установлен: {percent}%")
        await show_referral_settings(msg, state)

    except ValueError:
        await msg.answer("❌ Неверный формат чисел")
    except Exception as e:
        await msg.answer(f"❌ Ошибка: {e}")


@router.message(StateFilter(AdminStates.editing_coefficients), F.text.startswith("/set_coeff"))
async def set_coefficient(msg: Message, state: FSMContext):
    """Изменить коэффициент доходности"""
    try:
        parts = msg.text.split()
        if len(parts) != 3:
            await msg.answer("❌ Формат: /set_coeff [пул] [коэффициент]")
            return

        pool_name = parts[1]
        coefficient = float(parts[2])

        if pool_name not in settings.POOL_COEFFICIENTS:
            await msg.answer(f"❌ Неизвестный пул: {pool_name}")
            return

        settings.POOL_COEFFICIENTS[pool_name] = coefficient

        await msg.answer(f"✅ Коэффициент {pool_name} установлен: {coefficient}")
        await show_coefficients(msg, state)

    except ValueError:
        await msg.answer("❌ Коэффициент должен быть числом")
    except Exception as e:
        await msg.answer(f"❌ Ошибка: {e}")