# =============================================================================
# Project     : Kanban — Tablero Kanban Open-Source
# File        : app/routers/auth.py
# Description : Auth router: login with password (bcrypt), OTP token
#               request and OTP verification endpoints. Manages JWT
#               session cookie.
# -----------------------------------------------------------------------------
# Author      : Hector Manuel Durante Nuñez
# Email       : hector_durante@yahoo.com.mx
# GitHub      : https://github.com/hdurante/Kanban
# License     : GNU AGPLv3 — See LICENSE file for details
# Created     : 2026-04-24
# Version     : 1.0.0
# =============================================================================
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.user import User
from app.services.auth import (
    authenticate_user,
    create_access_token,
    create_otp_token,
    validate_otp_token,
)
from app.services.email import send_otp_email
from app.dependencies import get_current_user
from app.config import settings

router = APIRouter(tags=["auth"])


def _templates():
    from app.main import templates
    return templates


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.cookies.get("access_token"):
        return RedirectResponse("/board", status_code=302)
    return _templates().TemplateResponse("login.html", {"request": request, "app_name": settings.app_name, "app_title_suffix": settings.app_title_suffix})


@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(db, email, password)
    if not user:
        return _templates().TemplateResponse(
            "login.html",
            {"request": request, "app_name": settings.app_name, "app_title_suffix": settings.app_title_suffix, "error": "Credenciales incorrectas"},
            status_code=400,
        )
    token = create_access_token({"sub": str(user.id), "role": user.role})
    response = RedirectResponse("/board", status_code=302)
    response.set_cookie(
        "access_token",
        token,
        httponly=True,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )
    return response


@router.post("/login/otp/request", response_class=HTMLResponse)
async def request_otp(
    request: Request,
    email: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == email, User.is_active == True))
    user = result.scalar_one_or_none()

    # Always respond the same to prevent email enumeration
    msg = "Si el correo existe recibirás un código de acceso."

    if user:
        plain_token = await create_otp_token(db, user)
        await send_otp_email(user.email, user.name, plain_token)

    return _templates().TemplateResponse(
        "login.html",
        {
            "request": request,
            "app_name": settings.app_name, "app_title_suffix": settings.app_title_suffix,
            "otp_sent": True,
            "otp_email": email,
            "otp_message": msg,
        },
    )


@router.post("/login/otp/verify", response_class=HTMLResponse)
async def verify_otp(
    request: Request,
    email: str = Form(...),
    token: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    user = await validate_otp_token(db, email, token)
    if not user:
        return _templates().TemplateResponse(
            "login.html",
            {
                "request": request,
                "app_name": settings.app_name, "app_title_suffix": settings.app_title_suffix,
                "otp_sent": True,
                "otp_email": email,
                "error": "Código inválido, expirado o sin usos disponibles.",
            },
            status_code=400,
        )
    jwt_token = create_access_token({"sub": str(user.id), "role": user.role})
    response = RedirectResponse("/board", status_code=302)
    response.set_cookie(
        "access_token",
        jwt_token,
        httponly=True,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("access_token")
    return response
