# =============================================================================
# Project     : Kanban — Tablero Kanban Open-Source
# File        : app/models/group.py
# Description : ORM model: Group. A group aggregates users and tickets
#               to provide scoped visibility on the Kanban board.
# -----------------------------------------------------------------------------
# Author      : Hector Manuel Durante Nuñez
# Email       : hector_durante@yahoo.com.mx
# GitHub      : https://github.com/hdurante/Kanban
# License     : GNU AGPLv3 — See LICENSE file for details
# Created     : 2026-04-24
# Version     : 1.0.0
# =============================================================================
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.user import user_group


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(500), nullable=True)

    users = relationship("User", secondary=user_group, back_populates="groups")
    tickets = relationship("Ticket", back_populates="group")
