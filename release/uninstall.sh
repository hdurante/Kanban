#!/usr/bin/env bash
set -euo pipefail

# Uninstall script for Kanban release deployment.
# Prompts for an optional database backup before removing containers and volumes.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_DIR="$SCRIPT_DIR/backup"

confirm() {
  local prompt="$1"
  local answer
  read -rp "$prompt [y/N]: " answer
  case "$answer" in
    [Yy]|[Yy][Ee][Ss]) return 0 ;; 
    *) return 1 ;;
  esac
}

if confirm "¿Deseas crear un respaldo de la base de datos antes de desinstalar?"; then
  mkdir -p "$BACKUP_DIR"
  echo "Creando respaldo en: $BACKUP_DIR"
  cd "$PROJECT_DIR"
  if [[ ! -x "$PROJECT_DIR/scripts/backup_db.sh" ]]; then
    echo "[ERROR] No se encontró el script de respaldo scripts/backup_db.sh"
    exit 1
  fi
  ./scripts/backup_db.sh "$BACKUP_DIR"
  echo "Respaldo completado en: $BACKUP_DIR"
else
  echo "Se omitió el respaldo de la base de datos."
fi

cd "$PROJECT_DIR"
if [[ ! -f docker-compose.release.yml ]]; then
  echo "[ERROR] No se encontró el archivo docker-compose.release.yml en $PROJECT_DIR"
  exit 1
fi

echo "Deteniendo y eliminando contenedores/volúmenes..."
docker compose -f docker-compose.release.yml down -v --remove-orphans

echo "Desinstalación completada."
if [[ -d "$BACKUP_DIR" ]]; then
  echo "Los respaldos quedaron en: $BACKUP_DIR"
fi
