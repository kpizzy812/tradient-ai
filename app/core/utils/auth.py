import hmac
import hashlib
import time
import json
from urllib.parse import parse_qsl, quote, urlencode
from jose import JWTError, jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.status import HTTP_401_UNAUTHORIZED
from app.core.config import settings
from app.core.db import SessionLocal
from app.models.users import User as DBUser
from app.core.logger import logger
from init_data_py import InitData
from urllib.parse import unquote_plus
from typing import Dict, Any

bearer_scheme = HTTPBearer()


def verify_init_data(init_data_raw: str, expires_in: int = 3600) -> dict:
    # парсим без предварительного декодирования
    items = parse_qsl(init_data_raw, keep_blank_values=True)
    data_dict = dict(items)

    init_hash = data_dict.pop('hash', None)
    if not init_hash:
        raise ValueError("Missing 'hash' in init data")

    # НЕ декодируй поле user вручную здесь
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(data_dict.items())
    )

    # секрет по XGEN-формуле
    secret_key = hmac.new(
        key=b"WebAppData",
        msg=settings.BOT_TOKEN.encode("utf-8"),
        digestmod=hashlib.sha256
    ).digest()

    calc_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode("utf-8"),
        digestmod=hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calc_hash, init_hash):
        raise ValueError("Hash mismatch")

    # auth_date проверка
    if "auth_date" in data_dict:
        import time
        if time.time() - int(data_dict["auth_date"]) > expires_in:
            raise ValueError("Init data expired")

    # и только ТЕПЕРЬ декодируем user
    import json
    data_dict["user"] = json.loads(data_dict["user"])

    return data_dict

def create_access_token(data: Dict[str, Any]) -> str:
    from jose import jwt
    payload = data.copy()
    payload["exp"] = int(time.time()) + settings.JWT_EXPIRE_SECONDS
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> Dict[str, Any]:
    from jose import JWTError, jwt
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(HTTP_401_UNAUTHORIZED, "Invalid token")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    token = credentials.credentials
    payload = decode_access_token(token)
    tg_id = payload.get("tg_id")
    if tg_id is None:
        logger.warning("JWT missing tg_id")
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid token")
    db = SessionLocal()
    user = db.query(DBUser).filter(DBUser.tg_id == tg_id).first()
    db.close()
    if not user:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="User not found")
    return user