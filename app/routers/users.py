# =============================================================================
# Project     : Kanban — Tablero Kanban Open-Source
# File        : app/routers/users.py
# Description : Users router: Admin-only CRUD for user management including
#               creation, editing (with optional password reset), group
#               assignment and deactivation/deletion.
# -----------------------------------------------------------------------------
# Author      : Hector Manuel Durante Nuñez
# Email       : hector_durante@yahoo.com.mx
# GitHub      : https://github.com/hdurante/Kanban
# License     : MIT — See LICENSE file for details
# Created     : 2026-04-24
# Version     : 1.0.0
# =============================================================================
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.group import Group
from app.models.ticket import Ticket
from app.models.user import User, UserRole, user_group
from app.services.auth import hash_password

router = APIRouter(prefix="/users", tags=["users"])


def _templates():
    from app.main import templates
    return templates


@router.get("", response_class=HTMLResponse)
async def list_users(
    request: Request,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).options(selectinload(User.groups)).order_by(User.name)
    )
    users = result.scalars().all()
    result = await db.execute(select(Group).order_by(Group.name))
    groups = result.scalars().all()
    return _templates().TemplateResponse(
        "users/list.html",
        {
            "request": request,
            "users": users,
            "groups": groups,
            "current_user": current_user,
            "roles": UserRole,
            "app_name": settings.app_name,
        },
    )


@router.get("/new", response_class=HTMLResponse)
async def new_user_form(
    request: Request,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Group).order_by(Group.name))
    groups = result.scalars().all()
    return _templates().TemplateResponse(
        "users/form.html",
        {
            "request": request,
            "user": None,
            "groups": groups,
            "roles": UserRole,
            "current_user": current_user,
            "app_name": settings.app_name,
        },
    )


@router.post("/new", response_class=HTMLResponse)
async def create_user(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form("usuario"),
    group_ids: list[int] = Form(default=[]),
    is_active: str = Form("on"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    # Check email uniqueness
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        result = await db.execute(select(Group).order_by(Group.name))
        groups = result.scalars().all()
        return _templates().TemplateResponse(
            "users/form.html",
            {
                "request": request,
                "user": None,
                "groups": groups,
                "roles": UserRole,
                "current_user": current_user,
                "error": "El email ya está registrado",
                "app_name": settings.app_name,
            },
            status_code=400,
        )

    new_user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role=UserRole(role),
        is_active=is_active == "on",
    )
    db.add(new_user)
    await db.flush()

    if group_ids:
        g_result = await db.execute(select(Group).where(Group.id.in_(group_ids)))
        groups_to_add = g_result.scalars().all()
        await db.execute(
            user_group.insert(),
            [{'user_id': new_user.id, 'group_id': g.id} for g in groups_to_add]
        )

    await db.commit()
    return RedirectResponse("/users", status_code=302)


@router.get("/{user_id}/edit", response_class=HTMLResponse)
async def edit_user_form(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).options(selectinload(User.groups)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    result = await db.execute(select(Group).order_by(Group.name))
    groups = result.scalars().all()
    return _templates().TemplateResponse(
        "users/form.html",
        {
            "request": request,
            "user": user,
            "groups": groups,
            "roles": UserRole,
            "current_user": current_user,
            "app_name": settings.app_name,
        },
    )


@router.post("/{user_id}/edit", response_class=HTMLResponse)
async def update_user(
    user_id: int,
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(""),
    role: str = Form("usuario"),
    group_ids: list[int] = Form(default=[]),
    is_active: str = Form("on"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).options(selectinload(User.groups)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Check email uniqueness (excluding self)
    existing = await db.execute(
        select(User).where(User.email == email, User.id != user_id)
    )
    if existing.scalar_one_or_none():
        result2 = await db.execute(select(Group).order_by(Group.name))
        groups = result2.scalars().all()
        return _templates().TemplateResponse(
            "users/form.html",
            {
                "request": request,
                "user": user,
                "groups": groups,
                "roles": UserRole,
                "current_user": current_user,
                "error": "El email ya está en uso",
                "app_name": settings.app_name,
            },
            status_code=400,
        )

    user.name = name
    user.email = email
    user.role = UserRole(role)
    user.is_active = is_active == "on"
    if password:
        user.password_hash = hash_password(password)

    if group_ids:
        g_result = await db.execute(select(Group).where(Group.id.in_(group_ids)))
        new_groups = g_result.scalars().all()
        await db.execute(user_group.delete().where(user_group.c.user_id == user.id))
        if new_groups:
            await db.execute(
                user_group.insert(),
                [{'user_id': user.id, 'group_id': g.id} for g in new_groups]
            )
    else:
        await db.execute(user_group.delete().where(user_group.c.user_id == user.id))

    await db.commit()
    return RedirectResponse("/users", status_code=302)


@router.post("/{user_id}/delete")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Unassign tickets
    t_result = await db.execute(
        select(Ticket).where(Ticket.assigned_to_id == user_id)
    )
    for ticket in t_result.scalars().all():
        ticket.assigned_to_id = None

    await db.delete(user)
    await db.commit()
    return RedirectResponse("/users", status_code=302)
