import hashlib
from sqlalchemy.orm import Session
from app.models.users import User
from app.core.config import settings
from app.locales.texts import TEXTS
from aiogram import Bot
from app.services.notify import notify_admins_withdraw_request
from app.models.investment_transfer import InvestmentTransfer  # добавь импорт
from datetime import timedelta

# Локализация
def t(key: str, lang: str = None) -> str:
    lang = lang or settings.DEFAULT_LANGUAGE
    return TEXTS.get(key, {}).get(lang, TEXTS.get(key, {}).get("en", key))

# Генерация уникального кода
def generate_ref_code(tg_id: int) -> str:
    return hashlib.sha256(str(tg_id).encode()).hexdigest()[:8]

# Начисление реферальных бонусов
def distribute_referral_rewards(db: Session, user: User, amount: float, bot: Bot):
    levels = settings.REFERRAL_LEVELS
    current = user

    for level, percent in enumerate(levels, start=1):
        current = db.query(User).filter(User.id == current.referrer_id).first()
        if not current:
            break

        reward = round(amount * percent / 100, 2)
        current.ref_balance += reward

        if bot:
            try:
                bot.send_message(
                    chat_id=current.tg_id,
                    text=t("ref_earned", current.lang).format(amount=reward, level=level)
                )
            except Exception as e:
                print(f"[referral_notify] Ошибка при отправке пользователю {current.tg_id}: {e}")


from app.models.investments import Investment
from datetime import datetime

def invest_user(db: Session, user: User, amount: float, pool_name: str, bot: Bot) -> bool:
    """Создаёт инвестицию и начисляет реф-бонусы"""
    try:
        # 1. Обновим общий депозит
        user.deposit_usd += amount

        # 2. Создаём новую инвестицию
        investment = Investment(
            user_id=user.id,
            amount_usd=amount,
            pool_name=pool_name,
            created_at=datetime.utcnow(),
            included_today=False  # будет включён на следующий день
        )
        db.add(investment)

        # 3. Реф-бонусы
        distribute_referral_rewards(db, user, amount, bot)

        db.commit()
        return True
    except Exception as e:
        print(f"[invest_user] Ошибка: {e}")
        db.rollback()
        return False

from app.models.deposit_request import DepositRequest

def create_deposit_request(db: Session, user: User, amount: float, pool: str, method: str) -> DepositRequest:
    request = DepositRequest(
        user_id=user.id,
        amount_usd=amount,
        pool_name=pool,
        method=method,
        status="pending"
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


from app.models.withdraw_request import WithdrawRequest
from datetime import datetime, timedelta

def get_withdraw_commission(days_since_deposit: int) -> float:
    """Возвращает комиссию по дням из config.WITHDRAW_TIERS"""
    best_match = 0
    for days in sorted(settings.WITHDRAW_TIERS):
        if days_since_deposit >= days:
            best_match = days
    return settings.WITHDRAW_TIERS[best_match]


async def create_withdraw_request(
    db: Session,
    user,
    amount_usd: float,
    source: str,
    method: str,
    details: str,
    bot: Bot = None,
    mode: str = None,  # "base" или "express"
    pool_name: str = None,  # обязательно для source == "investment"
    days_since_deposit: int = 0
) -> WithdrawRequest:
    now = datetime.utcnow()

    if source == "balance":
        commission = 0.0
        execute_until = now + timedelta(days=1)

    elif source == "investment":
        if not pool_name:
            raise ValueError("pool_name обязателен при source='investment'")

        if mode == "express":
            commission = settings.WITHDRAW_EXPRESS_FEE
            execute_until = now + timedelta(days=1)
        else:
            commission = get_withdraw_commission(days_since_deposit)
            execute_until = now + timedelta(days=settings.WITHDRAW_BASE_DAYS)

        # Суммируем активные инвестиции
        investments = db.query(Investment).filter_by(
            user_id=user.id,
            pool_name=pool_name,
            is_active=True
        ).order_by(Investment.created_at).all()

        total_invested = sum(i.amount_usd for i in investments)
        if total_invested < amount_usd:
            raise ValueError("Недостаточно активных инвестиций в пуле")

        # Снимаем ровно amount_usd, не больше
        remaining = amount_usd
        for inv in investments:
            if remaining <= 0:
                break
            if inv.amount_usd <= remaining:
                # полностью списываем эту инвестицию
                remaining -= inv.amount_usd
                inv.is_active = False
            else:
                # частично списываем
                inv.amount_usd -= remaining
                remaining = 0
                # оставляем inv.is_active=True, т.к. часть суммы осталась
                break

    else:
        raise ValueError("Invalid source")

    # Комиссия
    final_amount = round(amount_usd * (1 - commission), 2)

    req = WithdrawRequest(
        user_id=user.id,
        source=source,
        mode=mode,
        amount_usd=amount_usd,
        final_amount_usd=final_amount,
        method=method,
        details=details,
        pool_name=pool_name if source == "investment" else None,
        status="pending",
        created_at=now,
        execute_until=execute_until
    )

    db.add(req)
    db.commit()
    db.refresh(req)

    if bot and method != "INTERNAL":
        try:
            await notify_admins_withdraw_request(bot, req, user)
        except Exception as e:
            print(f"⚠️ Ошибка при уведомлении админа: {e}")

    return req


async def withdraw_from_investment_to_balance(
    db: Session,
    user: User,
    amount_usd: float,
    pool_name: str,
    mode: str,
    days_since_deposit: int = 0
) -> float:
    now = datetime.utcnow()

    if mode == "express":
        commission = settings.WITHDRAW_EXPRESS_FEE
    else:
        commission = get_withdraw_commission(days_since_deposit)

    final_amount = round(amount_usd * (1 - commission), 2)

    # Списываем инвестиции
    investments = db.query(Investment).filter_by(
        user_id=user.id,
        pool_name=pool_name,
        is_active=True
    ).order_by(Investment.created_at).all()

    total_invested = sum(i.amount_usd for i in investments)
    if total_invested < amount_usd:
        raise ValueError("Недостаточно активных инвестиций в пуле")

    remaining = amount_usd
    for inv in investments:
        if remaining <= 0:
            break
        if inv.amount_usd <= remaining:
            remaining -= inv.amount_usd
            inv.is_active = False
        else:
            inv.amount_usd -= remaining
            remaining = 0
            break

    if mode == "express":
        commission = settings.WITHDRAW_EXPRESS_FEE
        execute_until = now + timedelta(days=1)
    else:
        commission = get_withdraw_commission(days_since_deposit)
        execute_until = now + timedelta(days=settings.WITHDRAW_BASE_DAYS)

    final_amount = round(amount_usd * (1 - commission), 2)

    # списываем инвестиции (как у тебя было)
    investments = db.query(Investment).filter_by(
        user_id=user.id,
        pool_name=pool_name,
        is_active=True
    ).order_by(Investment.created_at).all()

    total_invested = sum(i.amount_usd for i in investments)
    if total_invested < amount_usd:
        raise ValueError("Недостаточно активных инвестиций в пуле")

    remaining = amount_usd
    for inv in investments:
        if remaining <= 0:
            break
        if inv.amount_usd <= remaining:
            remaining -= inv.amount_usd
            inv.is_active = False
        else:
            inv.amount_usd -= remaining
            remaining = 0
            break

    # создаём отложенную запись
    transfer = InvestmentTransfer(
        user_id=user.id,
        pool_name=pool_name,
        amount_usd=amount_usd,
        final_amount_usd=final_amount,
        mode=mode,
        status="pending",
        created_at=now,
        execute_until=execute_until
    )

    db.add(transfer)
    db.commit()

    return final_amount