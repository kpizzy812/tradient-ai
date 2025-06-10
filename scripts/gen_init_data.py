import hmac
import hashlib
import time
import json
from urllib.parse import urlencode

BOT_TOKEN = "8024565295:AAGmWeXeWmK3xD8xBu0e9dFss_iMFb7fUXk"

def make_init_data(user_id: int, username: str = None, first_name: str = None, language_code: str = "en"):
    now = int(time.time())
    user = {"id": user_id}
    if username:     user["username"] = username
    if first_name:   user["first_name"] = first_name
    user["language_code"] = language_code

    data = {
        "user": json.dumps(user, separators=(",", ":")),
        "auth_date": str(now)
    }
    # собираем check_string
    check_string = "\n".join(f"{k}={data[k]}" for k in sorted(data))
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    signature = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()

    data["hash"] = signature
    return urlencode(data)

if __name__ == "__main__":
    # подставь свой user_id (любой Telegram ID), username и т.д.
    init_data = make_init_data(
        user_id=6084633525,
        username="Kpeezy4L",
        first_name="Kpeezy",
        language_code="en"
    )
    print(init_data)
