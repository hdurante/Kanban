# =============================================================================
# Project     : Kanban — Tablero Kanban Open-Source
# File        : app/schemas/status.py
# Description : Pydantic schemas for Status CRUD. Includes validation to
#               prevent using reserved IDs 1 and 999.
# -----------------------------------------------------------------------------
# Author      : Hector Manuel Durante Nuñez
# Email       : hector_durante@yahoo.com.mx
# GitHub      : https://github.com/hdurante/Kanban
# License     : MIT — See LICENSE file for details
# Created     : 2026-04-24
# Version     : 1.0.0
# =============================================================================
from typing import Optional

from pydantic import BaseModel, field_validator


class StatusCreate(BaseModel):
    id: int  # The order number (2-998)
    name: str

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: int) -> int:
        if v < 2 or v > 998:
            raise ValueError("Status order must be between 2 and 998 (1 and 999 are reserved)")
        return v


class StatusUpdate(BaseModel):
    name: Optional[str] = None


class StatusRead(BaseModel):
    id: int
    name: str
    is_locked: bool

    model_config = {"from_attributes": True}
