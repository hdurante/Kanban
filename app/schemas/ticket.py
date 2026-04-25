# =============================================================================
# Project     : Kanban — Tablero Kanban Open-Source
# File        : app/schemas/ticket.py
# Description : Pydantic schemas for Ticket CRUD, board card rendering
#               (compact view) and status/assignment changes.
# -----------------------------------------------------------------------------
# Author      : Hector Manuel Durante Nuñez
# Email       : hector_durante@yahoo.com.mx
# GitHub      : https://github.com/hdurante/Kanban
# License     : MIT — See LICENSE file for details
# Created     : 2026-04-24
# Version     : 1.0.0
# =============================================================================
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.ticket import Priority


class TicketCreate(BaseModel):
    title: str
    description: Optional[str] = None
    reference: Optional[str] = None
    priority: Priority = Priority.normal
    status_id: int = 1
    group_id: int
    estimated_date: Optional[datetime] = None
    estimated_cost: Optional[int] = None  # minutes
    assigned_to_id: Optional[int] = None
    requested_by_id: Optional[int] = None


class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    reference: Optional[str] = None
    priority: Optional[Priority] = None
    group_id: Optional[int] = None
    estimated_date: Optional[datetime] = None
    estimated_cost: Optional[int] = None
    assigned_to_id: Optional[int] = None
    requested_by_id: Optional[int] = None


class TicketStatusChange(BaseModel):
    status_id: int


class TicketAssignChange(BaseModel):
    assigned_to_id: Optional[int] = None


class TicketCard(BaseModel):
    """Minimal data for board card rendering."""

    id: int
    title: str
    reference: Optional[str] = None
    priority: Priority
    status_id: int
    group_id: int
    group_name: str
    assigned_to_id: Optional[int] = None
    assigned_to_name: Optional[str] = None
    estimated_date: Optional[datetime] = None
    is_overdue: bool = False
    effective_color: str = "normal"

    model_config = {"from_attributes": True}


class TicketRead(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    reference: Optional[str] = None
    priority: Priority
    status_id: int
    group_id: int
    group_name: str
    estimated_date: Optional[datetime] = None
    estimated_cost: Optional[int] = None
    created_at: datetime
    finished_at: Optional[datetime] = None
    created_by_id: int
    created_by_name: str
    assigned_to_id: Optional[int] = None
    assigned_to_name: Optional[str] = None
    requested_by_id: Optional[int] = None
    requested_by_name: Optional[str] = None
    is_overdue: bool = False
    effective_color: str = "normal"

    model_config = {"from_attributes": True}
