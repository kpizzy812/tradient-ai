import hmac
import hashlib

bot_token = "8024565295:AAGmWeXeWmK3xD8xBu0e9dFss_iMFb7fUXk"  # ← без кавычек, не скрывай ничего
data_check_string = """auth_date=1747656615
chat_instance=1114930785646171240
chat_type=private
user={"id":6084633525,"first_name":"Kpeezy","last_name":"","username":"Kpeezy4L","language_code":"ru","is_premium":true,"allows_write_to_pm":true,"photo_url":"https://t.me/i/userpic/320/ekDdXhawScIXYTyrCboYQJ6tKcsceVJ4lcyTtXo-2hbDLZfPNgaMMEA7-lICtyx-.svg"}"""

# 1. Секретный ключ (по доке!)
secret_key = hmac.new(
    key=b"WebAppData",
    msg=bot_token.encode(),
    digestmod=hashlib.sha256
).digest()

# 2. Считаем hash
calc_hash = hmac.new(
    key=secret_key,
    msg=data_check_string.encode(),
    digestmod=hashlib.sha256
).hexdigest()

print("✅ calc_hash =", calc_hash)
