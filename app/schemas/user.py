# =============================================================================
# Project     : Kanban — Tablero Kanban Open-Source
# File        : app/schemas/user.py
# Description : Pydantic schemas for User CRUD: create, update, read and
#               compact list representation.
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

from pydantic import BaseModel, EmailStr

from app.models.user import UserRole


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.usuario
    group_ids: list[int] = []


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    group_ids: Optional[list[int]] = None


class UserRead(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    group_ids: list[int] = []

    model_config = {"from_attributes": True}


class UserInList(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    is_active: bool

    model_config = {"from_attributes": True}
