#!/usr/bin/env bash
set -euo pipefail

# Определяем дефолтную ветку origin (main/master)
BASE_BRANCH=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@' || echo main)
git fetch origin "$BASE_BRANCH" >/dev/null 2>&1 || true

# Список изменённых файлов
CHANGED=$(git diff --name-status "origin/${BASE_BRANCH}"...HEAD | grep -E "migrations/.*\.py" || true)

# Если миграций нет — ок
[ -z "$CHANGED" ] && exit 0

# Правило:
# - Разрешены только НОВЫЕ миграции (статус 'A' = Added)
# - Любые изменения существующих ('M' Modified, 'D' Deleted, 'R' Renamed и т.п.) — ❌
BAD=$(echo "$CHANGED" | awk '$1!="A"{print}')
if [ -n "$BAD" ]; then
  echo "❌ Запрещено редактировать/удалять уже существующие миграции:"
  echo "$BAD"
  echo "Разрешены только новые файлы (Added) в каталогах */migrations/*.py"
  exit 1
fi

echo "✅ Миграции в порядке: только новые файлы добавлены."