# =============================================================================
# Project     : Kanban — Tablero Kanban Open-Source
# File        : app/models/__init__.py
# Description : Models package — re-exports all ORM models so Alembic
#               auto-discovers them for migration generation.
# -----------------------------------------------------------------------------
# Author      : Hector Manuel Durante Nuñez
# Email       : hector_durante@yahoo.com.mx
# GitHub      : https://github.com/hdurante/Kanban
# License     : MIT — See LICENSE file for details
# Created     : 2026-04-24
# Version     : 1.0.0
# =============================================================================
from app.models.user import User, OTPToken, user_group, UserRole
from app.models.group import Group
from app.models.status import Status
from app.models.ticket import Ticket, TicketStatusHistory, Priority
from app.models.system_config import SystemConfig
from app.models.reference_number import ReferenceNumber

__all__ = [
    "User",
    "OTPToken",
    "user_group",
    "UserRole",
    "Group",
    "Status",
    "Ticket",
    "TicketStatusHistory",
    "Priority",
    "SystemConfig",
    "ReferenceNumber",
]
