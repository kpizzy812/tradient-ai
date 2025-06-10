from sqlalchemy.orm import Session
from app.models.users import User
from app.models.deposit_request import DepositRequest
from app.models.withdraw_request import WithdrawRequest


def get_root_referrer(db: Session, user: User) -> User:
    """Находит самого верхнего в цепочке приглашений"""
    current = user
    while current.referrer_id:
        next_user = db.query(User).filter(User.id == current.referrer_id).first()
        if not next_user:
            break
        current = next_user
    return current


def get_referral_counts(db: Session, user: User, levels: int = 5) -> dict[int, int]:
    """Возвращает число партнёров по уровням"""
    counts = {i: 0 for i in range(1, levels + 1)}
    current_level = [user]
    for level in range(1, levels + 1):
        next_level = []
        for u in current_level:
            children = db.query(User).filter(User.referrer_id == u.id).all()
            counts[level] += len(children)
            next_level.extend(children)
        current_level = next_level
    return counts


def get_active_referrals_count(db: Session, user: User, levels: int = 5) -> int:
    """Считает всех активных рефералов на 5 уровней вниз"""
    active = 0
    current_level = [user]
    for _ in range(levels):
        next_level = []
        for u in current_level:
            children = db.query(User).filter(User.referrer_id == u.id).all()
            for c in children:
                if c.deposit_usd > 0:
                    active += 1
            next_level.extend(children)
        current_level = next_level
    return active


def get_total_deposits(db: Session, user_id: int) -> float:
    return db.query(DepositRequest).filter_by(user_id=user_id, status="approved")\
        .with_entities(DepositRequest.amount_usd).all() or 0.0


def get_total_withdrawals(db: Session, user_id: int) -> float:
    return db.query(WithdrawRequest).filter_by(user_id=user_id, status="approved")\
        .with_entities(WithdrawRequest.final_amount_usd).all() or 0.0
