# =============================================================================
# Project     : Kanban — Tablero Kanban Open-Source
# File        : app/models/ticket.py
# Description : ORM models: Ticket (main work item) and TicketStatusHistory
#               (audit log of state transitions). Defines Priority enum.
# -----------------------------------------------------------------------------
# Author      : Hector Manuel Durante Nuñez
# Email       : hector_durante@yahoo.com.mx
# GitHub      : https://github.com/hdurante/Kanban
# License     : MIT — See LICENSE file for details
# Created     : 2026-04-24
# Version     : 1.0.0
# =============================================================================
import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Priority(str, enum.Enum):
    prioritario = "prioritario"  # red   — never overridden
    alto = "alto"                # yellow
    normal = "normal"            # green
    bajo = "bajo"                # gray
    # "retrasado" (purple) is computed at display time when
    # estimated_date < today AND priority != prioritario


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    reference = Column(String(100), nullable=True)  # Jira / external ticket ref

    priority = Column(Enum(Priority), default=Priority.normal, nullable=False)
    status_id = Column(Integer, ForeignKey("statuses.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)

    estimated_date = Column(DateTime(timezone=True), nullable=True)
    estimated_cost = Column(Integer, nullable=True)  # minutes

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)

    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    status = relationship("Status", back_populates="tickets")
    group = relationship("Group", back_populates="tickets")
    creator = relationship("User", foreign_keys=[created_by_id], back_populates="created_tickets")
    assignee = relationship("User", foreign_keys=[assigned_to_id], back_populates="assigned_tickets")
    requester = relationship("User", foreign_keys=[requested_by_id], back_populates="requested_tickets")
    status_history = relationship(
        "TicketStatusHistory",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketStatusHistory.changed_at",
    )


class TicketStatusHistory(Base):
    __tablename__ = "ticket_status_history"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    old_status_id = Column(Integer, ForeignKey("statuses.id", ondelete="SET NULL"), nullable=True)
    new_status_id = Column(Integer, ForeignKey("statuses.id", ondelete="SET NULL"), nullable=True)
    changed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    changed_at = Column(DateTime(timezone=True), server_default=func.now())

    ticket = relationship("Ticket", back_populates="status_history")
    old_status = relationship("Status", foreign_keys=[old_status_id])
    new_status = relationship("Status", foreign_keys=[new_status_id])
    changed_by = relationship("User", foreign_keys=[changed_by_id])
