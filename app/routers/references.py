# =============================================================================
# Project     : Kanban — Tablero Kanban Open-Source
# File        : app/routers/references.py
# Description : Reference numbers router: catalog management for reusable
#               external reference values used by tickets.
# -----------------------------------------------------------------------------
# Author      : Hector Manuel Durante Nuñez
# Email       : hector_durante@yahoo.com.mx
# GitHub      : https://github.com/hdurante/Kanban
# License     : MIT — See LICENSE file for details
# Created     : 2026-04-28
# Version     : 1.0.0
# =============================================================================
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import settings
from app.database import get_db
from app.dependencies import require_lider_or_above
from app.models.reference_number import ReferenceNumber
from app.models.user import User

router = APIRouter(prefix="/references", tags=["references"])


def _templates():
    from app.main import templates
    return templates


@router.get("", response_class=HTMLResponse)
async def references_page(
    request: Request,
    current_user: User = Depends(require_lider_or_above),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ReferenceNumber).order_by(ReferenceNumber.value.asc()))
    references = result.scalars().all()

    return _templates().TemplateResponse(
        "references/index.html",
        {
            "request": request,
            "current_user": current_user,
            "references": references,
            "app_name": settings.app_name,
            "app_title_suffix": settings.app_title_suffix,
        },
    )


@router.post("", response_class=HTMLResponse)
async def create_reference(
    value: str = Form(...),
    current_user: User = Depends(require_lider_or_above),
    db: AsyncSession = Depends(get_db),
):
    clean_value = value.strip()
    if not clean_value:
        raise HTTPException(status_code=400, detail="La referencia no puede estar vacia")
    if len(clean_value) > 100:
        raise HTTPException(status_code=400, detail="La referencia no puede exceder 100 caracteres")

    exists = await db.execute(select(ReferenceNumber).where(ReferenceNumber.value == clean_value))
    if not exists.scalar_one_or_none():
        db.add(ReferenceNumber(value=clean_value, created_by_id=current_user.id))
        await db.commit()

    return RedirectResponse("/references", status_code=302)


@router.post("/{reference_id}/delete")
async def delete_reference(
    reference_id: int,
    current_user: User = Depends(require_lider_or_above),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ReferenceNumber).where(ReferenceNumber.id == reference_id))
    reference = result.scalar_one_or_none()
    if reference:
        await db.delete(reference)
        await db.commit()
    return RedirectResponse("/references", status_code=302)
