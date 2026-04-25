# =============================================================================
# Project     : Kanban — Tablero Kanban Open-Source
# File        : app/schemas/__init__.py
# Description : Schemas package — re-exports all Pydantic schemas for
#               convenient imports across the application.
# -----------------------------------------------------------------------------
# Author      : Hector Manuel Durante Nuñez
# Email       : hector_durante@yahoo.com.mx
# GitHub      : https://github.com/hdurante/Kanban
# License     : MIT — See LICENSE file for details
# Created     : 2026-04-24
# Version     : 1.0.0
# =============================================================================
from app.schemas.auth import Token, LoginForm, OTPRequestForm, OTPLoginForm
from app.schemas.user import UserCreate, UserRead, UserUpdate, UserInList
from app.schemas.group import GroupCreate, GroupRead, GroupUpdate
from app.schemas.status import StatusCreate, StatusRead, StatusUpdate
from app.schemas.ticket import TicketCreate, TicketRead, TicketUpdate, TicketCard, TicketStatusChange

__all__ = [
    "Token",
    "LoginForm",
    "OTPRequestForm",
    "OTPLoginForm",
    "UserCreate",
    "UserRead",
    "UserUpdate",
    "UserInList",
    "GroupCreate",
    "GroupRead",
    "GroupUpdate",
    "StatusCreate",
    "StatusRead",
    "StatusUpdate",
    "TicketCreate",
    "TicketRead",
    "TicketUpdate",
    "TicketCard",
    "TicketStatusChange",
]
