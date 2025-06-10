#!/bin/bash

SERVER="root@193.233.254.29"
REMOTE_DIR="/home/tradient-ai"

function sync_project {
  echo "🔁 Синхронизация проекта..."
  rsync -azP \
    --delete \
    --exclude '.venv' \
    --exclude 'venv' \
    --exclude '.next' \
    --exclude 'node_modules' \
    --exclude '.git' \
    --exclude '__pycache__' \
    ./ "$SERVER:$REMOTE_DIR/"
}

function remote_exec {
  ssh $SERVER "$1"
}

function build_project {
  echo "🔨 Настройка проекта на сервере..."

  remote_exec "
    set -e
    cd $REMOTE_DIR &&
    python3 -m venv venv &&
    source venv/bin/activate &&
    pip install --upgrade pip &&
    pip install -r requirements.txt &&
    cd frontend &&
    rm -rf node_modules package-lock.json &&
    npm install &&
    npm run build
  "
}

function start_services {
  remote_exec "
    cd $REMOTE_DIR &&
    source venv/bin/activate &&

    pm2 delete tradient-api tradient-front tradient-bot || true &&

    pm2 start \"venv/bin/uvicorn app.api.main:app --host 0.0.0.0 --port 8000\" --name tradient-api &&
    pm2 start \"npm run start\" --name tradient-front --cwd frontend &&
    pm2 start \"venv/bin/python3 -m app.bot.run\" --name tradient-bot &&

    pm2 save
  "
}





function stop_services {
  remote_exec "pm2 stop all"
}

function restart_services {
  remote_exec "pm2 restart all"
}

function show_logs {
  remote_exec "pm2 logs"
}

while true; do
  echo ""
  echo "=== Tradient AI Control Panel ==="
  echo "[1] Sync project to server"
  echo "[2] Build (venv, deps, build frontend)"
  echo "[3] Start all services"
  echo "[4] Restart all services"
  echo "[5] Stop all services"
  echo "[6] View logs"
  echo "[7] Exit"
  echo "================================="
  read -p "Выбери действие: " option

  case $option in
    1) sync_project ;;
    2) build_project ;;
    3) start_services ;;
    4) restart_services ;;
    5) stop_services ;;
    6) show_logs ;;
    7) echo "👋 Пока!"; exit ;;
    *) echo "❌ Неверный ввод" ;;
  esac
done
