# =============================================================================
# Project     : Kanban — Tablero Kanban Open-Source
# File        : app/routers/tickets.py
# Description : Tickets router: full CRUD, drag-and-drop status changes,
#               assignment handling, priority management and audit history.
#               Enforces role-based edit permissions per ticket.
# -----------------------------------------------------------------------------
# Author      : Hector Manuel Durante Nuñez
# Email       : hector_durante@yahoo.com.mx
# GitHub      : https://github.com/hdurante/Kanban
# License     : MIT — See LICENSE file for details
# Created     : 2026-04-24
# Version     : 1.0.0
# =============================================================================
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user, require_usuario_or_above
from app.models.group import Group
from app.models.status import Status
from app.models.ticket import Ticket, TicketStatusHistory, Priority
from app.models.user import User, UserRole, user_group

router = APIRouter(prefix="/tickets", tags=["tickets"])

PRIORITY_LABELS = {
    "prioritario": "Prioritario",
    "alto": "Alto",
    "normal": "Normal",
    "bajo": "Bajo",
}


def _templates():
    from app.main import templates
    return templates


def _compute_effective_color(ticket: Ticket) -> str:
    if ticket.priority.value == "prioritario":
        return "prioritario"
    if ticket.estimated_date:
        est = ticket.estimated_date
        if est.tzinfo is None:
            est = est.replace(tzinfo=timezone.utc)
        if est < datetime.now(timezone.utc):
            return "retrasado"
    return ticket.priority.value


async def _can_edit_ticket(current_user: User, ticket: Ticket) -> bool:
    """Check if the current user is allowed to edit a ticket."""
    if current_user.role in (UserRole.admin, UserRole.lider):
        return True
    if current_user.role == UserRole.colaborador:
        return ticket.assigned_to_id == current_user.id or ticket.created_by_id == current_user.id
    return False


async def _load_ticket(db: AsyncSession, ticket_id: int) -> Ticket:
    result = await db.execute(
        select(Ticket)
        .options(
            selectinload(Ticket.status),
            selectinload(Ticket.group),
            selectinload(Ticket.assignee),
            selectinload(Ticket.creator),
            selectinload(Ticket.requester),
            selectinload(Ticket.status_history).selectinload(TicketStatusHistory.old_status),
            selectinload(Ticket.status_history).selectinload(TicketStatusHistory.new_status),
            selectinload(Ticket.status_history).selectinload(TicketStatusHistory.changed_by),
        )
        .where(Ticket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


# ── Create ──────────────────────────────────────────────────────────────────


@router.get("/new", response_class=HTMLResponse)
async def new_ticket_form(
    request: Request,
    current_user: User = Depends(require_usuario_or_above),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Group))
    groups = result.scalars().all()
    result = await db.execute(select(User).where(User.is_active == True).order_by(User.name))
    users = result.scalars().all()
    result = await db.execute(select(Status).order_by(Status.id))
    statuses = result.scalars().all()

    # Load user's first group id to pre-select in form (avoids lazy-load in template)
    ug_result = await db.execute(
        select(user_group.c.group_id)
        .where(user_group.c.user_id == current_user.id)
        .limit(1)
    )
    user_default_group_id = ug_result.scalar_one_or_none()

    return _templates().TemplateResponse(
        "tickets/form.html",
        {
            "request": request,
            "current_user": current_user,
            "user_default_group_id": user_default_group_id,
            "groups": groups,
            "users": users,
            "statuses": statuses,
            "priorities": PRIORITY_LABELS,
            "ticket": None,
            "app_name": settings.app_name,
        },
    )


@router.post("/new", response_class=HTMLResponse)
async def create_ticket(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    reference: str = Form(""),
    priority: str = Form("normal"),
    group_id: int = Form(...),
    estimated_date: str = Form(""),
    estimated_cost: str = Form(""),
    assigned_to_id: str = Form(""),
    requested_by_id: str = Form(""),
    current_user: User = Depends(require_usuario_or_above),
    db: AsyncSession = Depends(get_db),
):
    est_date = None
    if estimated_date:
        try:
            est_date = datetime.fromisoformat(estimated_date).replace(tzinfo=timezone.utc)
        except ValueError:
            pass

    ticket = Ticket(
        title=title,
        description=description or None,
        reference=reference or None,
        priority=Priority(priority),
        status_id=1,
        group_id=group_id,
        estimated_date=est_date,
        estimated_cost=int(estimated_cost) if estimated_cost else None,
        assigned_to_id=int(assigned_to_id) if assigned_to_id else None,
        requested_by_id=int(requested_by_id) if requested_by_id else None,
        created_by_id=current_user.id,
    )
    db.add(ticket)
    await db.flush()

    history = TicketStatusHistory(
        ticket_id=ticket.id,
        old_status_id=None,
        new_status_id=1,
        changed_by_id=current_user.id,
    )
    db.add(history)
    await db.commit()
    return RedirectResponse("/board", status_code=302)


# ── Detail / Edit ────────────────────────────────────────────────────────────


@router.get("/{ticket_id}", response_class=HTMLResponse)
async def ticket_detail(
    ticket_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ticket = await _load_ticket(db, ticket_id)
    ticket._effective_color = _compute_effective_color(ticket)
    can_edit = await _can_edit_ticket(current_user, ticket)

    result = await db.execute(select(Group))
    groups = result.scalars().all()
    result = await db.execute(select(User).where(User.is_active == True).order_by(User.name))
    users = result.scalars().all()
    result = await db.execute(select(Status).order_by(Status.id))
    statuses = result.scalars().all()

    return _templates().TemplateResponse(
        "tickets/detail.html",
        {
            "request": request,
            "ticket": ticket,
            "current_user": current_user,
            "can_edit": can_edit,
            "groups": groups,
            "users": users,
            "statuses": statuses,
            "priorities": PRIORITY_LABELS,
            "app_name": settings.app_name,
        },
    )


@router.post("/{ticket_id}/edit", response_class=HTMLResponse)
async def edit_ticket(
    ticket_id: int,
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    reference: str = Form(""),
    priority: str = Form("normal"),
    group_id: int = Form(...),
    estimated_date: str = Form(""),
    estimated_cost: str = Form(""),
    assigned_to_id: str = Form(""),
    requested_by_id: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ticket = await _load_ticket(db, ticket_id)
    if not await _can_edit_ticket(current_user, ticket):
        raise HTTPException(status_code=403, detail="No tienes permiso para editar este ticket")

    ticket.title = title
    ticket.description = description or None
    ticket.reference = reference or None
    ticket.priority = Priority(priority)
    ticket.group_id = group_id
    ticket.estimated_cost = int(estimated_cost) if estimated_cost else None
    ticket.assigned_to_id = int(assigned_to_id) if assigned_to_id else None
    ticket.requested_by_id = int(requested_by_id) if requested_by_id else None

    if estimated_date:
        try:
            ticket.estimated_date = datetime.fromisoformat(estimated_date).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    else:
        ticket.estimated_date = None

    await db.commit()
    return RedirectResponse(f"/tickets/{ticket_id}", status_code=302)


# ── Status change (drag & drop + manual) ────────────────────────────────────


@router.post("/{ticket_id}/status", response_class=HTMLResponse)
async def change_status(
    ticket_id: int,
    request: Request,
    status_id: int = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ticket = await _load_ticket(db, ticket_id)

    if not await _can_edit_ticket(current_user, ticket):
        raise HTTPException(status_code=403, detail="Sin permiso")

    # Verify status exists
    st_result = await db.execute(select(Status).where(Status.id == status_id))
    new_status = st_result.scalar_one_or_none()
    if not new_status:
        raise HTTPException(status_code=400, detail="Estado inválido")

    old_status_id = ticket.status_id
    ticket.status_id = status_id

    if status_id == 999 and not ticket.finished_at:
        ticket.finished_at = datetime.now(timezone.utc)
    elif status_id != 999:
        ticket.finished_at = None

    history = TicketStatusHistory(
        ticket_id=ticket.id,
        old_status_id=old_status_id,
        new_status_id=status_id,
        changed_by_id=current_user.id,
    )
    db.add(history)
    await db.commit()

    # Return the updated card partial for HTMX
    await db.refresh(ticket)
    result_t = await db.execute(
        select(Ticket)
        .options(selectinload(Ticket.group), selectinload(Ticket.assignee), selectinload(Ticket.status))
        .where(Ticket.id == ticket_id)
    )
    ticket = result_t.scalar_one()
    ticket._effective_color = _compute_effective_color(ticket)

    result_u = await db.execute(select(User).where(User.is_active == True).order_by(User.name))
    all_users = result_u.scalars().all()

    return _templates().TemplateResponse(
        "board/_card.html",
        {"request": request, "ticket": ticket, "current_user": current_user, "all_users": all_users},
    )


# ── Assign ───────────────────────────────────────────────────────────────────


@router.post("/{ticket_id}/assign", response_class=HTMLResponse)
async def assign_ticket(
    ticket_id: int,
    request: Request,
    assigned_to_id: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ticket = await _load_ticket(db, ticket_id)

    # Anyone can take unassigned; only assignee/leader/admin can reassign
    if ticket.assigned_to_id and not await _can_edit_ticket(current_user, ticket):
        raise HTTPException(status_code=403, detail="Sin permiso para reasignar")

    ticket.assigned_to_id = int(assigned_to_id) if assigned_to_id else None
    await db.commit()

    await db.refresh(ticket)
    result_t = await db.execute(
        select(Ticket)
        .options(selectinload(Ticket.group), selectinload(Ticket.assignee), selectinload(Ticket.status))
        .where(Ticket.id == ticket_id)
    )
    ticket = result_t.scalar_one()
    ticket._effective_color = _compute_effective_color(ticket)

    result_u = await db.execute(select(User).where(User.is_active == True).order_by(User.name))
    all_users = result_u.scalars().all()

    return _templates().TemplateResponse(
        "board/_card.html",
        {"request": request, "ticket": ticket, "current_user": current_user, "all_users": all_users},
    )


# ── Delete ───────────────────────────────────────────────────────────────────


@router.post("/{ticket_id}/delete")
async def delete_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ticket = await _load_ticket(db, ticket_id)
    if not await _can_edit_ticket(current_user, ticket):
        raise HTTPException(status_code=403, detail="Sin permiso")
    await db.delete(ticket)
    await db.commit()
    return RedirectResponse("/board", status_code=302)
