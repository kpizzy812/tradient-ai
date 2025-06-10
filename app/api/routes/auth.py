from fastapi import APIRouter, HTTPException, Header, Depends
from starlette.status import HTTP_401_UNAUTHORIZED
from pydantic import BaseModel
from app.core.utils.auth import verify_init_data, create_access_token, decode_access_token
from app.core.db import SessionLocal
from app.models.users import User as DBUser
from app.core.logger import logger

router = APIRouter()

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/login", response_model=TokenResponse)
async def login(authorization: str = Header(..., description="tma <init_data>")):
    logger.info("[/auth/login] header=%s", authorization)

    # 1. Схема и init_data
    try:
        scheme, init_data = authorization.split(" ", 1)
    except ValueError:
        raise HTTPException(HTTP_401_UNAUTHORIZED, "Invalid authorization header")
    if scheme.lower() != "tma":
        raise HTTPException(HTTP_401_UNAUTHORIZED, "Invalid authorization scheme")

    logger.debug(f"raw init_data: {init_data}")

    # 2. Верифицируем init_data
    try:
        data = verify_init_data(init_data)
    except ValueError as e:
        logger.warning(f"[auth] init_data error: {e}")
        raise HTTPException(status_code=401, detail=str(e))

    logger.info("[/auth/login] init_data valid for user %s", data["user"]["id"])

    # 3. Работа с БД
    tg = data["user"]
    tg_id = int(tg["id"])
    db = SessionLocal()
    user = db.query(DBUser).filter(DBUser.tg_id == tg_id).first()
    if not user:
        user = DBUser(tg_id=tg_id, username=tg.get("username"), lang=tg.get("language_code", "en"))
        db.add(user)
        logger.info("[/auth/login] created user %s", tg_id)
    else:
        user.username = tg.get("username")
        user.lang = tg.get("language_code", "en")
        logger.info("[/auth/login] updated user %s", tg_id)
    db.commit()
    db.refresh(user)
    db.close()

    # 4. Генерируем JWT и возвращаем
    token = create_access_token({"tg_id": tg_id})
    logger.info("[/auth/login] issued token for %s", tg_id)
    return TokenResponse(access_token=token)