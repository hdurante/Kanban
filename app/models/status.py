# =============================================================================
# Project     : Kanban — Tablero Kanban Open-Source
# File        : app/models/status.py
# Description : ORM model: Status. Represents a Kanban board column.
#               IDs 1 and 999 are locked (Por Hacer / Terminado).
# -----------------------------------------------------------------------------
# Author      : Hector Manuel Durante Nuñez
# Email       : hector_durante@yahoo.com.mx
# GitHub      : https://github.com/hdurante/Kanban
# License     : GNU AGPLv3 — See LICENSE file for details
# Created     : 2026-04-24
# Version     : 1.0.0
# =============================================================================
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Status(Base):
    __tablename__ = "statuses"

    id = Column(Integer, primary_key=True)  # the order number (1-999)
    name = Column(String(100), unique=True, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)  # True for id=1 and id=999

    tickets = relationship("Ticket", back_populates="status")
