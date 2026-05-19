# =============================================================================
# Project     : Kanban — Tablero Kanban Open-Source
# File        : app/routers/statuses.py
# Description : Statuses router: Admin-only CRUD for Kanban column management.
#               Locked states (1, 999) cannot be deleted. Orphan tickets
#               from deleted states are moved to state 1 automatically.
# -----------------------------------------------------------------------------
# Author      : Hector Manuel Durante Nuñez
# Email       : hector_durante@yahoo.com.mx
# GitHub      : https://github.com/hdurante/Kanban
# License     : GNU AGPLv3 — See LICENSE file for details
# Created     : 2026-04-24
# Version     : 1.0.0
# =============================================================================
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import settings
from app.database import get_db
from app.dependencies import require_admin, url_for
from app.models.status import Status
from app.models.ticket import Ticket
from app.models.user import User

router = APIRouter(prefix="/statuses", tags=["statuses"])


def _templates():
    from app.main import templates
    return templates


@router.get("", response_class=HTMLResponse)
async def list_statuses(
    request: Request,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Status).order_by(Status.id))
    statuses = result.scalars().all()
    return _templates().TemplateResponse(
        "statuses/list.html",
        {
            "request": request,
            "statuses": statuses,
            "current_user": current_user,
            "app_name": settings.app_name, "app_title_suffix": settings.app_title_suffix,
        },
    )


@router.post("/new", response_class=HTMLResponse)
async def create_status(
    request: Request,
    order: int = Form(...),
    name: str = Form(...),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if order < 2 or order > 998:
        result = await db.execute(select(Status).order_by(Status.id))
        statuses = result.scalars().all()
        return _templates().TemplateResponse(
            "statuses/list.html",
            {
                "request": request,
                "statuses": statuses,
                "current_user": current_user,
                "error": "El orden debe estar entre 2 y 998",
                "app_name": settings.app_name, "app_title_suffix": settings.app_title_suffix,
            },
            status_code=400,
        )

    existing = await db.execute(select(Status).where(Status.id == order))
    if existing.scalar_one_or_none():
        result = await db.execute(select(Status).order_by(Status.id))
        statuses = result.scalars().all()
        return _templates().TemplateResponse(
            "statuses/list.html",
            {
                "request": request,
                "statuses": statuses,
                "current_user": current_user,
                "error": f"Ya existe un estado con el orden {order}",
                "app_name": settings.app_name, "app_title_suffix": settings.app_title_suffix,
            },
            status_code=400,
        )

    status = Status(id=order, name=name, is_locked=False)
    db.add(status)
    await db.commit()
    return RedirectResponse(url_for("/statuses"), status_code=302)


@router.post("/{status_id}/edit", response_class=HTMLResponse)
async def edit_status(
    status_id: int,
    request: Request,
    name: str = Form(...),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Status).where(Status.id == status_id))
    status = result.scalar_one_or_none()
    if not status:
        raise HTTPException(status_code=404, detail="Estado no encontrado")
    status.name = name
    await db.commit()
    return RedirectResponse(url_for("/statuses"), status_code=302)


@router.post("/{status_id}/delete")
async def delete_status(
    status_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Status).where(Status.id == status_id))
    status = result.scalar_one_or_none()
    if not status:
        raise HTTPException(status_code=404, detail="Estado no encontrado")
    if status.is_locked:
        raise HTTPException(status_code=400, detail="Este estado no puede eliminarse")

    # Move orphan tickets to status 1
    t_result = await db.execute(select(Ticket).where(Ticket.status_id == status_id))
    for ticket in t_result.scalars().all():
        ticket.status_id = 1

    await db.delete(status)
    await db.commit()
    return RedirectResponse(url_for("/statuses"), status_code=302)
