#!/usr/bin/env bash
set -euo pipefail

# Restores a SQL backup into the docker-compose PostgreSQL service.
# Usage:
#   ./scripts/restore_db.sh backups/kanban_20260426_101500.sql
#   ./scripts/restore_db.sh backups/kanban_20260426_101500.sql --drop-public

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <backup.sql> [--drop-public]"
  exit 1
fi

BACKUP_FILE="$1"
DROP_PUBLIC="${2:-}"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "Backup file not found: $BACKUP_FILE"
  exit 1
fi

cd "$PROJECT_DIR"

if [[ "$DROP_PUBLIC" == "--drop-public" ]]; then
  echo "Dropping and recreating public schema..."
  docker compose exec -T db psql -v ON_ERROR_STOP=1 -U kanban -d kanban -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
fi

echo "Restoring backup: $BACKUP_FILE"
cat "$BACKUP_FILE" | docker compose exec -T db psql -v ON_ERROR_STOP=1 -U kanban -d kanban
echo "Restore completed successfully."
