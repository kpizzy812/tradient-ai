from datetime import datetime
from app.core.db import SessionLocal
from app.models.investment_transfer import InvestmentTransfer
from app.models.users import User
from app.core.logger import logger

async def process_pending_transfers_loop():
    from asyncio import sleep
    while True:
        try:
            db = SessionLocal()
            now = datetime.utcnow()
            transfers = db.query(InvestmentTransfer).filter_by(status="pending").filter(
                InvestmentTransfer.execute_until <= now
            ).all()

            for t in transfers:
                user = db.query(User).get(t.user_id)
                if not user:
                    continue

                user.profit_usd += t.final_amount_usd
                t.status = "completed"
                logger.info(f"[transfer] +${t.final_amount_usd} → user_id={user.id}")

            db.commit()
            db.close()

        except Exception as e:
            logger.error(f"[transfer] Ошибка при начислении: {e}")

        await sleep(60 * 10)  # каждые 10 минут
