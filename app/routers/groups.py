# =============================================================================
# Project     : Kanban — Tablero Kanban Open-Source
# File        : app/routers/groups.py
# Description : Groups router: Admin-only CRUD for group management.
#               Groups define ticket visibility scope per user.
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
from app.dependencies import require_admin, get_current_user, url_for
from app.models.group import Group
from app.models.user import User

router = APIRouter(prefix="/groups", tags=["groups"])


def _templates():
    from app.main import templates
    return templates


@router.get("", response_class=HTMLResponse)
async def list_groups(
    request: Request,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Group).order_by(Group.name))
    groups = result.scalars().all()
    return _templates().TemplateResponse(
        "groups/list.html",
        {"request": request, "groups": groups, "current_user": current_user, "app_name": settings.app_name, "app_title_suffix": settings.app_title_suffix},
    )


@router.post("/new", response_class=HTMLResponse)
async def create_group(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(Group).where(Group.name == name))
    if existing.scalar_one_or_none():
        result = await db.execute(select(Group).order_by(Group.name))
        groups = result.scalars().all()
        return _templates().TemplateResponse(
            "groups/list.html",
            {
                "request": request,
                "groups": groups,
                "current_user": current_user,
                "error": "Ya existe un grupo con ese nombre",
                "app_name": settings.app_name, "app_title_suffix": settings.app_title_suffix,
            },
            status_code=400,
        )
    group = Group(name=name, description=description or None)
    db.add(group)
    await db.commit()
    return RedirectResponse(url_for("/groups"), status_code=302)


@router.post("/{group_id}/edit", response_class=HTMLResponse)
async def edit_group(
    group_id: int,
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    group.name = name
    group.description = description or None
    await db.commit()
    return RedirectResponse(url_for("/groups"), status_code=302)


@router.post("/{group_id}/delete")
async def delete_group(
    group_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    await db.delete(group)
    await db.commit()
    return RedirectResponse(url_for("/groups"), status_code=302)
