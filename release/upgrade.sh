#!/bin/bash
set -e

# --- Kanban Upgrade Script ---

if [ ! -f .env ] || [ ! -f docker-compose.release.yml ]; then
  echo "[!] No se detectó una instalación previa."
  if [ -f install.sh ]; then
    echo "→ Ejecutando install.sh para instalación inicial..."
    bash install.sh
    exit 0
  else
    echo "Por favor ejecuta primero install.sh para instalar."
    exit 1
  fi
fi

# Pull nueva imagen y reiniciar
KANBAN_IMAGE_TAG=${KANBAN_IMAGE_TAG:-latest}
echo "Actualizando imagen Docker (tag: $KANBAN_IMAGE_TAG)..."
docker compose -f docker-compose.release.yml pull

echo "Levantando contenedores con la nueva versión..."
docker compose -f docker-compose.release.yml up -d

echo "\nUpgrade completado. Puedes acceder a la app normalmente."
