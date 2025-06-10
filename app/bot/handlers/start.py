from aiogram import Router, F
from aiogram.types import Message
from app.core.db import SessionLocal
from app.core.config import settings
from app.services.logic import t, generate_ref_code
from app.models.users import User
from app.core.logger import logger
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

# @router.message()
# async def debug_thread_id(message: Message):
#     print(f"chat_id={message.chat.id}, thread_id={message.message_thread_id}")

@router.message(F.text.startswith("/start"))
async def cmd_start(msg: Message):
    db = SessionLocal()
    tg_id = msg.from_user.id
    username = msg.from_user.username
    lang = msg.from_user.language_code or settings.DEFAULT_LANGUAGE
    args = msg.text.split(" ")

    user = db.query(User).filter(User.tg_id == tg_id).first()
    if not user:
        referrer = None
        if len(args) == 2:
            ref_code = args[1].strip()
            referrer = db.query(User).filter(User.ref_code == ref_code).first()

        user = User(
            tg_id=tg_id,
            username=username,
            lang=lang,
            referrer_id=referrer.id if referrer else None,
            ref_code=generate_ref_code(tg_id),
        )
        db.add(user)
        db.commit()

        if referrer:
            try:
                await msg.bot.send_message(
                    chat_id=referrer.tg_id,
                    text=t("new_ref", referrer.lang).format(name=msg.from_user.full_name)
                )
            except Exception as e:
                logger.warning(f"⚠️ Ошибка при уведомлении реферала: {e}")

    db.close()
    photo_url = "https://i.ibb.co/twtxYGJG/Chat-GPT-Image-31-2025-14-30-32.png"  # замени на свой

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=t("launch_app", lang),
                url=f"https://t.me/{settings.BOT_USERNAME}?startapp"
            )
        ],
        [
            InlineKeyboardButton(
                text=t("support", lang),
                url=settings.SUPPORT_URL
            )
        ]
    ])

    await msg.answer_photo(
        photo=photo_url,
        caption=t("start_description", lang),
        reply_markup=keyboard
    )


# @router.message(F.text.startswith("/set_yield "))
# async def cmd_set_yield(msg: Message):
#     if msg.from_user.id not in settings.ADMIN_TG_IDS:
#         return await msg.answer(t("not_admin", msg.from_user.language_code))
#
#     try:
#         value = float(msg.text.split()[1])
#     except:
#         return await msg.answer("❌ Пример: /set_yield 3.1")
#
#     from app.services.yielding import distribute_daily_yield
#
#     db = SessionLocal()
#     try:
#         distribute_daily_yield(db, value)
#         await msg.answer(f"✅ Установлена доходность: {value}%")
#     finally:
#         db.close()
