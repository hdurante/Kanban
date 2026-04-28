# =============================================================================
# Project     : Kanban — Tablero Kanban Open-Source
# File        : app/schemas/auth.py
# Description : Pydantic schemas for authentication: JWT Token response,
#               password login form, OTP request and OTP verification.
# -----------------------------------------------------------------------------
# Author      : Hector Manuel Durante Nuñez
# Email       : hector_durante@yahoo.com.mx
# GitHub      : https://github.com/hdurante/Kanban
# License     : GNU AGPLv3 — See LICENSE file for details
# Created     : 2026-04-24
# Version     : 1.0.0
# =============================================================================
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginForm(BaseModel):
    email: str
    password: str


class OTPRequestForm(BaseModel):
    email: str


class OTPLoginForm(BaseModel):
    email: str
    token: str
