#!/bin/bash

set -e

mkdir -p logs

echo "🐍 Запуск FastAPI (API backend)..."
uvicorn app.api.main:app --reload > logs/api.log 2>&1 &
UVICORN_RELOADER_PID=$!
sleep 2

# Найдём PID дочернего процесса (реальный сервер)
UVICORN_CHILD_PID=$(pgrep -P $UVICORN_RELOADER_PID)

echo "🤖 Запуск Telegram-бота..."
python -m app.bot.run > logs/bot.log 2>&1 &
BOT_PID=$!
sleep 1

# Проверка
ps -p $UVICORN_CHILD_PID > /dev/null || echo "❌ FastAPI не запустился!"
ps -p $BOT_PID > /dev/null || echo "❌ Бот не запустился!"

trap 'echo "🛑 Остановка..."; \
ps -p $BOT_PID > /dev/null && kill $BOT_PID 2>/dev/null; \
ps -p $UVICORN_RELOADER_PID > /dev/null && kill $UVICORN_RELOADER_PID 2>/dev/null; \
ps -p $UVICORN_CHILD_PID > /dev/null && kill $UVICORN_CHILD_PID 2>/dev/null; \
wait; exit 0' SIGINT SIGTERM

wait


# ngrok http 3000 | npm run dev -- --host 0.0.0.0
# tail -f logs/api.log logs/bot.log
