# =============================================================================
# Project     : Kanban — Tablero Kanban Open-Source
# File        : app/main.py
# Description : FastAPI application factory: lifespan, router registration
#               and first-boot seed data (default statuses + admin user).
# -----------------------------------------------------------------------------
# Author      : Hector Manuel Durante Nuñez
# Email       : hector_durante@yahoo.com.mx
# GitHub      : https://github.com/hdurante/Kanban
# License     : GNU AGPLv3 — See LICENSE file for details
# Created     : 2026-04-24
# Version     : 1.0.0
# =============================================================================
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text

from app.config import settings
from app.database import Base, engine
from app.routers import auth, board, groups, references, settings as settings_router, statuses, tickets, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (use Alembic in production for migrations)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Backward-compatible schema adjustments for existing databases.
        await conn.execute(
            text("ALTER TABLE tickets ADD COLUMN IF NOT EXISTS progress_percentage INTEGER NOT NULL DEFAULT 0")
        )

    # Seed default data
    from app.database import AsyncSessionLocal
    from app.models.status import Status
    from app.models.user import User, UserRole
    from app.models.system_config import SystemConfig
    from app.services.auth import hash_password
    from sqlalchemy.future import select

    async with AsyncSessionLocal() as db:
        # Create locked statuses if not exist
        default_statuses = [
            Status(id=1, name="Por Hacer", is_locked=True),
            Status(id=2, name="En Progreso", is_locked=False),
            Status(id=3, name="Pausado", is_locked=False),
            Status(id=999, name="Terminado", is_locked=True),
        ]
        for st in default_statuses:
            existing = await db.execute(select(Status).where(Status.id == st.id))
            if not existing.scalar_one_or_none():
                db.add(st)

        # Create default admin user if no users exist
        user_count = await db.execute(select(User))
        if not user_count.scalars().first():
            admin = User(
                name="Administrador",
                email="admin@kanban.local",
                password_hash=hash_password("admin1234"),
                role=UserRole.admin,
                is_active=True,
            )
            db.add(admin)

        await db.commit()

    yield


app = FastAPI(
    title=settings.app_name,
    description="Tablero Kanban — Open Source",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/api/docs" if settings.debug else None,
    redoc_url=None,
)

templates = Jinja2Templates(directory="app/templates")
templates.env.globals["app_version"] = settings.app_version
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(board.router)
app.include_router(tickets.router)
app.include_router(users.router)
app.include_router(groups.router)
app.include_router(statuses.router)
app.include_router(references.router)
app.include_router(settings_router.router)


@app.api_route("/sw.js", methods=["GET", "HEAD"], include_in_schema=False)
async def service_worker():
    sw_template = Path("app/static/sw.js").read_text(encoding="utf-8")
    sw_content = sw_template.replace("__APP_VERSION__", settings.app_version)
    # Must be served from root to control navigation requests across the app.
    return Response(
        content=sw_content,
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"},
    )


@app.api_route("/manifest.webmanifest", methods=["GET", "HEAD"], include_in_schema=False)
async def webmanifest():
    return FileResponse(
        "app/static/manifest.webmanifest",
        media_type="application/manifest+json",
    )


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    if request.cookies.get("access_token"):
        return RedirectResponse("/board", status_code=302)
    return RedirectResponse("/login", status_code=302)
