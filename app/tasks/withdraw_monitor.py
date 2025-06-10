import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.withdraw_request import WithdrawRequest
from app.models.users import User
from app.core.logger import logger


async def withdraw_monitor_loop():
    while True:
        try:
            db: Session = SessionLocal()
            now = datetime.utcnow()

            pending = db.query(WithdrawRequest).filter(
                WithdrawRequest.status == "pending",
                WithdrawRequest.execute_until <= now
            ).all()

            for req in pending:
                if req.source != "investment":
                    # Пропускаем ручные заявки с баланса
                    logger.info(f"⏩ Пропущена заявка #{req.id} (ручная выплата)")
                    continue

                try:
                    user = db.query(User).filter_by(id=req.user_id).first()
                    if not user:
                        logger.warning(f"⚠️ Пользователь не найден для заявки #{req.id}")
                        continue

                    user.profit_usd += req.final_amount_usd
                    req.status = "auto_paid"

                    db.commit()
                    logger.success(f"✅ Автовыплата: user_id={user.id}, +{req.final_amount_usd} $ (заявка #{req.id})")
                except Exception as e:
                    db.rollback()
                    logger.error(f"❌ Ошибка при начислении выплаты по заявке #{req.id}: {e}")

            db.close()
        except Exception as e:
            logger.error(f"❌ Ошибка в withdraw_monitor: {e}")

        await asyncio.sleep(60)  # каждые 60 сек