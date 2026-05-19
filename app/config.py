# =============================================================================
# Project     : Kanban — Tablero Kanban Open-Source
# File        : app/config.py
# Description : Application settings loaded from environment variables
#               and .env file using Pydantic BaseSettings.
# -----------------------------------------------------------------------------
# Author      : Hector Manuel Durante Nuñez
# Email       : hector_durante@yahoo.com.mx
# GitHub      : https://github.com/hdurante/Kanban
# License     : GNU AGPLv3 — See LICENSE file for details
# Created     : 2026-04-24
# Version     : 1.0.0
# =============================================================================
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://kanban:kanban@localhost:5432/kanban"

    # Security
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480  # 8 hours

    # OTP
    otp_length: int = 16
    otp_max_uses: int = 99
    otp_expire_days: int = 30

    # Email (SMTP)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_tls: bool = True

    # Board
    completed_hide_days: int = 7

    # App
    app_name: str = "Kanban"
    app_title_suffix: str = ""  # e.g., "Mi Empresa" -> "Kanban + Mi Empresa"
    app_version: str = "1.0.0"
    app_base_path: str = ""  # e.g., "/kanban" for https://site.com/kanban
    debug: bool = False

    model_config = {"env_file": ".env"}


settings = Settings()
