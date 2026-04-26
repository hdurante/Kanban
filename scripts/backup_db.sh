#!/usr/bin/env bash
set -euo pipefail

# Creates a SQL backup from the docker-compose PostgreSQL service.
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${1:-$PROJECT_DIR/backups}"
TIMESTAMP="$(date +"%Y%m%d_%H%M%S")"
OUTPUT_FILE="$BACKUP_DIR/kanban_${TIMESTAMP}.sql"

mkdir -p "$BACKUP_DIR"
cd "$PROJECT_DIR"

echo "Creating backup in: $OUTPUT_FILE"
docker compose exec -T db pg_dump -U kanban -d kanban > "$OUTPUT_FILE"
echo "Backup created successfully: $OUTPUT_FILE"
