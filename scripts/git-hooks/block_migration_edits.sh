#!/usr/bin/env bash
set -euo pipefail

# Проверяем ТОЛЬКО индексированные (staged) файлы
CHANGED=$(git diff --cached --name-status | grep -E "migrations/.*\.py" || true)

[ -z "$CHANGED" ] && exit 0

# Разрешаем только добавление новых миграций в staged
BAD=$(echo "$CHANGED" | awk '$1!="A"{print}')
if [ -n "$BAD" ]; then
  echo "❌ Нельзя изменять/удалять существующие миграции в pre-commit:"
  echo "$BAD"
  echo "Разрешены только новые файлы (Added) под */migrations/*.py"
  exit 1
fi

echo "✅ Pre-commit: миграции — только новые файлы."