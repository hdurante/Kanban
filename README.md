# Kanban

Open-source Kanban board built with **FastAPI**, **PostgreSQL**, **HTMX**, and **SortableJS**.

## Features

- Configurable columns/states (1 = Por Hacer, 999 = Terminado are fixed)
- Color-coded tickets by priority (🔴 Prioritario, 🟡 Alto, 🟢 Normal, ⚫ Bajo, 🟣 Retrasado-auto)
- Drag & drop cards between columns
- Role-based access: Lector, Usuario, Colaborador, Líder, Admin
- Login by password or one-time token (OTP) sent by email
- Group-based ticket visibility
- External ticket reference field (Jira, etc.)
- Admin panel: users, groups, states, system config
- Docker-first deployment

---

## Quick Start (Docker)

```bash
# 1. Clone
git clone https://github.com/your-org/kanban.git
cd kanban

# 2. Configure environment
cp .env.example .env
# Edit .env and set SECRET_KEY and SMTP settings

# 3. Start
docker compose up -d

# 4. Open http://localhost:8000
#    Default credentials: admin@kanban.local / admin1234
#    ⚠️  Change the password immediately after first login!
```

---

## Local Development (without Docker)

```bash
# Requires Python 3.12+ and a running PostgreSQL instance

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env — set DATABASE_URL to point to your local Postgres

uvicorn app.main:app --reload
```

The app creates all tables and seeds default statuses + admin user on first boot.

---

## Project Structure

```
app/
  main.py            — FastAPI app & startup
  config.py          — Settings (Pydantic BaseSettings)
  database.py        — Async SQLAlchemy engine & session
  dependencies.py    — Auth & role dependencies
  models/            — SQLAlchemy ORM models
  schemas/           — Pydantic schemas
  services/          — Auth (JWT/bcrypt/OTP) & Email helpers
  routers/           — FastAPI route handlers
  templates/         — Jinja2 HTML templates
  static/            — CSS & JavaScript
alembic/             — Database migration scripts
scripts/             — Utility scripts (create_admin.py)
docker-compose.yml
Dockerfile
```

---

## Default Admin Credentials

| Email | Password |
|-------|----------|
| `admin@kanban.local` | `admin1234` |

> **Change these immediately** after your first login via `/users`.

---

## Configuration

All settings can be changed in the **Admin → Configuración** panel or via `.env` / Docker environment variables. Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | *(required)* | JWT signing key — must be long and random |
| `DATABASE_URL` | `postgresql+asyncpg://kanban:kanban@db:5432/kanban` | Postgres connection |
| `COMPLETED_HIDE_DAYS` | `7` | Days before hiding finished tickets |
| `OTP_MAX_USES` | `99` | Maximum uses per OTP token |
| `OTP_EXPIRE_DAYS` | `30` | OTP validity in days |
| `SMTP_*` | — | Email settings for OTP delivery |

---

## License

MIT — see [LICENSE](LICENSE).
