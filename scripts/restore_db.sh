#!/usr/bin/env bash
set -euo pipefail

# Restores a SQL backup into the docker-compose PostgreSQL service.
# Usage:
#   ./scripts/restore_db.sh backups/kanban_20260426_101500.sql
#   ./scripts/restore_db.sh backups/kanban_20260426_101500.sql --drop-public
#   ./scripts/restore_db.sh backups/kanban_20260426_101500.sql --clean

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <backup.sql> [--drop-public|--clean]"
  exit 1
fi

BACKUP_FILE="$1"
MODE="${2:-}"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -n "$MODE" && "$MODE" != "--drop-public" && "$MODE" != "--clean" ]]; then
  echo "Unknown option: $MODE"
  echo "Usage: $0 <backup.sql> [--drop-public|--clean]"
  exit 1
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "Backup file not found: $BACKUP_FILE"
  exit 1
fi

# Keep a stable absolute path before changing directories.
BACKUP_FILE="$(cd "$(dirname "$BACKUP_FILE")" && pwd)/$(basename "$BACKUP_FILE")"

cd "$PROJECT_DIR"

if [[ "$MODE" == "--drop-public" || "$MODE" == "--clean" ]]; then
  echo "Dropping and recreating public schema..."
  docker compose exec -T db psql -v ON_ERROR_STOP=1 -U kanban -d kanban -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
fi

echo "Restoring backup: $BACKUP_FILE"
if ! cat "$BACKUP_FILE" | docker compose exec -T db psql -v ON_ERROR_STOP=1 -U kanban -d kanban; then
  echo ""
  echo "Restore failed. This usually means the destination DB already has objects."
  echo "Try again with a clean restore:"
  echo "  ./restore_db.sh $BACKUP_FILE --clean"
  exit 1
fi
echo "Restore completed successfully."
