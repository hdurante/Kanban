# =============================================================================
# Project     : Kanban — Tablero Kanban Open-Source
# File        : app/routers/board.py
# Description : Board router: main Kanban board view with group-scoped
#               ticket loading, filtering (priority, assignee, text search)
#               and column rendering.
# -----------------------------------------------------------------------------
# Author      : Hector Manuel Durante Nuñez
# Email       : hector_durante@yahoo.com.mx
# GitHub      : https://github.com/hdurante/Kanban
# License     : MIT — See LICENSE file for details
# Created     : 2026-04-24
# Version     : 1.0.0
# =============================================================================
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.group import Group
from app.models.status import Status
from app.models.ticket import Ticket
from app.models.user import User, UserRole

router = APIRouter(tags=["board"])


def _templates():
    from app.main import templates
    return templates


def _compute_effective_color(ticket: Ticket) -> str:
    """Returns the effective display color for a ticket."""
    if ticket.priority.value == "prioritario":
        return "prioritario"
    if ticket.estimated_date:
        est = ticket.estimated_date
        if est.tzinfo is None:
            est = est.replace(tzinfo=timezone.utc)
        if est < datetime.now(timezone.utc):
            return "retrasado"
    return ticket.priority.value


def _is_overdue(ticket: Ticket) -> bool:
    if not ticket.estimated_date:
        return False
    est = ticket.estimated_date
    if est.tzinfo is None:
        est = est.replace(tzinfo=timezone.utc)
    return est < datetime.now(timezone.utc)


@router.get("/board", response_class=HTMLResponse)
async def board(
    request: Request,
    group_id: str | None = None,
    priority: str | None = None,
    assigned_to: str | None = None,
    search: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Convert empty strings to None and parse integers
    try:
        group_id = int(group_id) if group_id and group_id.strip() else None
    except (ValueError, AttributeError):
        group_id = None
    
    try:
        assigned_to = int(assigned_to) if assigned_to and assigned_to.strip() else None
    except (ValueError, AttributeError):
        assigned_to = None
    
    # Clean up empty strings in string params
    priority = priority.strip() if priority and priority.strip() else None
    search = search.strip() if search and search.strip() else None

    # Load user with groups
    result = await db.execute(
        select(User).options(selectinload(User.groups)).where(User.id == current_user.id)
    )
    user = result.scalar_one()

    # Load all statuses ordered
    result = await db.execute(select(Status).order_by(Status.id))
    statuses = result.scalars().all()

    # Determine visible group IDs for current user
    if current_user.role == UserRole.admin:
        result = await db.execute(select(Group))
        all_groups = result.scalars().all()
        user_group_ids = [g.id for g in all_groups]
    else:
        user_group_ids = [g.id for g in user.groups]

    # Filter group if requested
    filter_group_ids = [group_id] if group_id and group_id in user_group_ids else user_group_ids

    # Build ticket query
    hide_before = datetime.now(timezone.utc).replace(tzinfo=None)
    from sqlalchemy import or_, and_, func as sqlfunc

    query = (
        select(Ticket)
        .options(
            selectinload(Ticket.group),
            selectinload(Ticket.assignee),
            selectinload(Ticket.status),
        )
        .where(Ticket.group_id.in_(filter_group_ids))
    )

    # Hide old completed tickets
    hide_days = settings.completed_hide_days
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(days=hide_days)
    query = query.where(
        or_(
            Ticket.status_id != 999,
            Ticket.finished_at > cutoff,
            Ticket.finished_at == None,
        )
    )

    if priority:
        query = query.where(Ticket.priority == priority)
    if assigned_to:
        query = query.where(Ticket.assigned_to_id == assigned_to)
    if search:
        query = query.where(Ticket.title.ilike(f"%{search}%"))

    result = await db.execute(query)
    tickets = result.scalars().all()

    # Enrich tickets with computed fields
    for ticket in tickets:
        ticket._effective_color = _compute_effective_color(ticket)
        ticket._is_overdue = _is_overdue(ticket)

    # Group tickets by status
    tickets_by_status = {s.id: [] for s in statuses}
    for ticket in tickets:
        if ticket.status_id in tickets_by_status:
            tickets_by_status[ticket.status_id].append(ticket)

    # Load all groups and users for filters
    result = await db.execute(select(Group).where(Group.id.in_(user_group_ids)))
    groups = result.scalars().all()

    result = await db.execute(select(User).where(User.is_active == True).order_by(User.name))
    all_users = result.scalars().all()

    return _templates().TemplateResponse(
        "board/index.html",
        {
            "request": request,
            "current_user": current_user,
            "statuses": statuses,
            "tickets_by_status": tickets_by_status,
            "groups": groups,
            "all_users": all_users,
            "user_group_ids": user_group_ids,
            "filter_group_id": group_id,
            "filter_priority": priority,
            "filter_assigned_to": assigned_to,
            "filter_search": search,
            "app_name": settings.app_name, "app_title_suffix": settings.app_title_suffix,
        },
    )
