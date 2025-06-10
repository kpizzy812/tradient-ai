function sync_project {
  echo "🔁 Синхронизация проекта..."
  rsync -azP \
    --delete \
    --exclude 'db.sqlite' \
    --exclude '.venv' \
    --exclude 'venv' \
    --exclude '.next' \
    --exclude 'node_modules' \
    --exclude '.git' \
    --exclude '__pycache__' \
    ./ root@193.233.254.29:/home/tradient-ai/
}
