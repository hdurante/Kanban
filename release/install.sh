#!/bin/bash
set -e

# --- Kanban Install Wizard ---

# Helper: generate random secret
random_secret() {
  tr -dc 'A-Za-z0-9!@#$%^&*()-_=+' </dev/urandom | head -c 48
}

# Helper: prompt with default
prompt() {
  local var="$1"; local msg="$2"; local def="$3"
  read -rp "$msg [$def]: " val
  eval $var="${val:-$def}"
}

# 1. Ask for config
prompt SECRET_KEY "SECRET_KEY para la app (dejar vacío para generar aleatorio)" ""
if [ -z "$SECRET_KEY" ]; then
  SECRET_KEY=$(random_secret)
  echo "  → Generado: $SECRET_KEY"
fi
prompt APP_PORT "Puerto para la app (8000 por default)" "8000"
prompt APP_BASE_PATH "Ruta virtual en nginx (ej. /kanban, o vacío para raíz)" ""
prompt POSTGRES_PORT "Puerto para Postgres (5432 por default)" "5432"
prompt ADMIN_EMAIL "Email admin inicial" "admin@kanban.local"
prompt ADMIN_PASSWORD "Clave admin inicial" "admin1234"

# 2. Copiar .env.example a .env y reemplazar valores
cp .env.example .env
sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" .env
sed -i "s|^DATABASE_URL=.*|DATABASE_URL=postgresql+asyncpg://kanban:kanban@db:$POSTGRES_PORT/kanban|" .env
sed -i "s|^APP_PORT=.*|APP_PORT=$APP_PORT|" .env
sed -i "s|^APP_BASE_PATH=.*|APP_BASE_PATH=$APP_BASE_PATH|" .env
sed -i "s|^POSTGRES_PORT=.*|POSTGRES_PORT=$POSTGRES_PORT|" .env

# 3. Mostrar resumen
cat <<EOF

Configuración lista:
  App:     http://localhost:$APP_PORT${APP_BASE_PATH}
  Ruta:    ${APP_BASE_PATH:-"raíz (/)"}
  Admin:   $ADMIN_EMAIL / $ADMIN_PASSWORD
  Postgres: puerto $POSTGRES_PORT
  SECRET_KEY: $SECRET_KEY

Iniciando contenedores...
EOF

# 4. Lanzar docker compose
KANBAN_IMAGE_TAG=${KANBAN_IMAGE_TAG:-latest}
docker compose -f docker-compose.release.yml up -d

echo "\nListo. Puedes acceder a http://localhost:$APP_PORT${APP_BASE_PATH:-/}"
