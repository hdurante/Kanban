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
# License     : GNU AGPLv3 — See LICENSE file for details
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
from app.models.reference_number import ReferenceNumber
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


def _parse_estimated_cost_hours(value: str) -> int | None:
    """Convert decimal hours (e.g. 0.5) to minutes for DB storage."""
    if not value:
        return None
    normalized = value.strip().replace(",", ".")
    if not normalized:
        return None
    try:
        hours = float(normalized)
    except ValueError:
        return None
    if hours < 0:
        return None
    return int(round(hours * 60))


def _parse_progress_percentage(value: str, default: int = 0) -> int:
    normalized = (value or "").strip()
    if not normalized:
        return default
    try:
        parsed = int(normalized)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="El porcentaje debe ser un entero") from exc
    if parsed < 0 or parsed > 100:
        raise HTTPException(status_code=400, detail="El porcentaje debe estar entre 0 y 100")
    return parsed


def _validate_ticket_text_fields(title: str, description: str) -> tuple[str, str]:
    title_clean = title.strip()
    if not title_clean:
        raise HTTPException(status_code=400, detail="El titulo es obligatorio")
    if len(title_clean) > 150:
        raise HTTPException(status_code=400, detail="El titulo no puede exceder 150 caracteres")
    description_clean = description or ""
    if len(description_clean) > 1000:
        raise HTTPException(status_code=400, detail="La descripcion no puede exceder 1000 caracteres")
    return title_clean, description_clean


async def _can_edit_ticket(current_user: User, ticket: Ticket) -> bool:
    """Check if the current user is allowed to edit a ticket."""
    if current_user.role in (UserRole.admin, UserRole.lider):
        return True
    if current_user.role == UserRole.colaborador:
        return ticket.assigned_to_id == current_user.id or ticket.created_by_id == current_user.id
    return False


def _can_edit_reference_value(current_user: User) -> bool:
    return current_user.role in (UserRole.admin, UserRole.lider)


async def _get_reference_values(db: AsyncSession) -> list[str]:
    result = await db.execute(select(ReferenceNumber).order_by(ReferenceNumber.value.asc()))
    return [r.value for r in result.scalars().all()]


async def _resolve_reference_value(
    db: AsyncSession,
    current_user: User,
    reference_select: str,
    reference_new: str,
    known_values: list[str],
) -> str | None:
    selected = (reference_select or "").strip()
    new_value = (reference_new or "").strip()
    known = set(known_values)

    if _can_edit_reference_value(current_user):
        candidate = new_value or selected
        if not candidate:
            return None
        if len(candidate) > 100:
            raise HTTPException(status_code=400, detail="La referencia no puede exceder 100 caracteres")
        if candidate not in known:
            db.add(ReferenceNumber(value=candidate, created_by_id=current_user.id))
        return candidate

    if selected and selected in known:
        return selected
    return None


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
    references = await _get_reference_values(db)

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
            "references": references,
            "can_edit_reference_value": _can_edit_reference_value(current_user),
            "app_name": settings.app_name, "app_title_suffix": settings.app_title_suffix,
        },
    )


@router.post("/new", response_class=HTMLResponse)
async def create_ticket(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    reference_select: str = Form(""),
    reference_new: str = Form(""),
    priority: str = Form("normal"),
    group_id: int = Form(...),
    estimated_date: str = Form(""),
    estimated_cost: str = Form(""),
    progress_percentage: str = Form("0"),
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

    title, description = _validate_ticket_text_fields(title, description)
    parsed_progress = _parse_progress_percentage(progress_percentage, default=0)
    references = await _get_reference_values(db)
    reference = await _resolve_reference_value(db, current_user, reference_select, reference_new, references)

    ticket = Ticket(
        title=title,
        description=description or None,
        reference=reference or None,
        priority=Priority(priority),
        status_id=1,
        group_id=group_id,
        estimated_date=est_date,
        estimated_cost=_parse_estimated_cost_hours(estimated_cost),
        progress_percentage=parsed_progress,
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
    references = await _get_reference_values(db)

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
            "references": references,
            "can_edit_reference_value": _can_edit_reference_value(current_user),
            "priorities": PRIORITY_LABELS,
            "app_name": settings.app_name, "app_title_suffix": settings.app_title_suffix,
        },
    )


@router.post("/{ticket_id}/edit", response_class=HTMLResponse)
async def edit_ticket(
    ticket_id: int,
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    reference_select: str = Form(""),
    reference_new: str = Form(""),
    priority: str = Form("normal"),
    group_id: int = Form(...),
    estimated_date: str = Form(""),
    estimated_cost: str = Form(""),
    progress_percentage: str = Form("0"),
    assigned_to_id: str = Form(""),
    requested_by_id: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ticket = await _load_ticket(db, ticket_id)
    if not await _can_edit_ticket(current_user, ticket):
        raise HTTPException(status_code=403, detail="No tienes permiso para editar este ticket")

    title, description = _validate_ticket_text_fields(title, description)
    references = await _get_reference_values(db)
    reference = await _resolve_reference_value(db, current_user, reference_select, reference_new, references)
    parsed_progress = _parse_progress_percentage(progress_percentage, default=ticket.progress_percentage)
    if ticket.status_id == 999:
        parsed_progress = 100

    ticket.title = title
    ticket.description = description or None
    ticket.reference = reference or None
    ticket.priority = Priority(priority)
    ticket.group_id = group_id
    ticket.estimated_cost = _parse_estimated_cost_hours(estimated_cost)
    ticket.progress_percentage = parsed_progress
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
        ticket.progress_percentage = 100
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
