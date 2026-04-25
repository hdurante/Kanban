# =============================================================================
# Project     : Kanban — Tablero Kanban Open-Source
# File        : app/models/system_config.py
# Description : ORM model: SystemConfig — key/value store for runtime
#               settings editable by admins through the UI.
# -----------------------------------------------------------------------------
# Author      : Hector Manuel Durante Nuñez
# Email       : hector_durante@yahoo.com.mx
# GitHub      : https://github.com/hdurante/Kanban
# License     : MIT — See LICENSE file for details
# Created     : 2026-04-24
# Version     : 1.0.0
# =============================================================================
from sqlalchemy import Column, String, Text

from app.database import Base


class SystemConfig(Base):
    """
    Key-value store for application settings editable by admins.
    Keys mirror the Settings class fields that should be configurable at runtime.
    """

    __tablename__ = "system_config"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    description = Column(String(500), nullable=True)
