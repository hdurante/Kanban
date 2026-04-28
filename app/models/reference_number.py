# =============================================================================
# Project     : Kanban — Tablero Kanban Open-Source
# File        : app/models/reference_number.py
# Description : ORM model for reusable external reference numbers used by
#               tickets (e.g., Jira IDs, folios, ticket numbers).
# -----------------------------------------------------------------------------
# Author      : Hector Manuel Durante Nuñez
# Email       : hector_durante@yahoo.com.mx
# GitHub      : https://github.com/hdurante/Kanban
# License     : GNU AGPLv3 — See LICENSE file for details
# Created     : 2026-04-28
# Version     : 1.0.0
# =============================================================================
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ReferenceNumber(Base):
    __tablename__ = "reference_numbers"
    __table_args__ = (UniqueConstraint("value", name="uq_reference_numbers_value"),)

    id = Column(Integer, primary_key=True, index=True)
    value = Column(String(100), nullable=False, unique=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    created_by = relationship("User")
