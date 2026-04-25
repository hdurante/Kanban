# =============================================================================
# Project     : Kanban — Tablero Kanban Open-Source
# File        : app/routers/settings.py
# Description : Settings router: Admin panel for system configuration.
#               Persists key/value settings to the DB and applies them
#               to the in-memory Settings object at runtime.
# -----------------------------------------------------------------------------
# Author      : Hector Manuel Durante Nuñez
# Email       : hector_durante@yahoo.com.mx
# GitHub      : https://github.com/hdurante/Kanban
# License     : MIT — See LICENSE file for details
# Created     : 2026-04-24
# Version     : 1.0.0
# =============================================================================
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import settings
from app.database import get_db
from app.dependencies import require_admin
from app.models.system_config import SystemConfig
from app.models.user import User

router = APIRouter(prefix="/settings", tags=["settings"])

DEFAULT_CONFIG = {
    "completed_hide_days": ("7", "Días para ocultar tickets terminados"),
    "otp_max_uses": ("99", "Usos máximos del token OTP"),
    "otp_expire_days": ("30", "Días de vigencia del token OTP"),
    "otp_length": ("16", "Longitud mínima del token OTP"),
    "smtp_host": ("smtp.gmail.com", "Servidor SMTP"),
    "smtp_port": ("587", "Puerto SMTP"),
    "smtp_user": ("", "Usuario SMTP / Email remitente"),
    "smtp_password": ("", "Contraseña SMTP"),
    "smtp_tls": ("true", "Usar TLS para SMTP (true/false)"),
    "app_name": ("Kanban", "Nombre de la aplicación"),
}


def _templates():
    from app.main import templates
    return templates


@router.get("", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SystemConfig))
    configs = {c.key: c for c in result.scalars().all()}
    return _templates().TemplateResponse(
        "settings/index.html",
        {
            "request": request,
            "configs": configs,
            "defaults": DEFAULT_CONFIG,
            "current_user": current_user,
            "app_name": settings.app_name,
        },
    )


@router.post("", response_class=HTMLResponse)
async def save_settings(
    request: Request,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    form = await request.form()
    result = await db.execute(select(SystemConfig))
    existing = {c.key: c for c in result.scalars().all()}

    for key in DEFAULT_CONFIG:
        value = form.get(key, "")
        if key in existing:
            existing[key].value = str(value)
        else:
            desc = DEFAULT_CONFIG[key][1]
            db.add(SystemConfig(key=key, value=str(value), description=desc))

    await db.commit()

    # Reload in-memory settings from DB
    for key in DEFAULT_CONFIG:
        value = form.get(key, "")
        if hasattr(settings, key):
            try:
                attr_type = type(getattr(settings, key))
                if attr_type == bool:
                    setattr(settings, key, str(value).lower() == "true")
                else:
                    setattr(settings, key, attr_type(value))
            except (ValueError, TypeError):
                pass

    return RedirectResponse("/settings", status_code=302)
