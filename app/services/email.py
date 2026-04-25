# =============================================================================
# Project     : Kanban — Tablero Kanban Open-Source
# File        : app/services/email.py
# Description : Email service: async OTP delivery via SMTP using aiosmtplib.
#               Falls back to console logging when SMTP is not configured
#               (development mode).
# -----------------------------------------------------------------------------
# Author      : Hector Manuel Durante Nuñez
# Email       : hector_durante@yahoo.com.mx
# GitHub      : https://github.com/hdurante/Kanban
# License     : MIT — See LICENSE file for details
# Created     : 2026-04-24
# Version     : 1.0.0
# =============================================================================
import logging

import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


async def send_otp_email(to_email: str, to_name: str, otp_token: str) -> bool:
    """
    Send an OTP token via email. Falls back to logging if SMTP is not configured.
    Returns True on success, False on failure.
    """
    if not settings.smtp_user or not settings.smtp_password:
        logger.warning(
            "SMTP not configured. OTP for %s: %s",
            to_email,
            otp_token,
        )
        return True  # In dev mode we consider it a success

    subject = f"[{settings.app_name}] Tu código de acceso temporal"
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto;">
      <h2 style="color: #3b5bdb;">{settings.app_name}</h2>
      <p>Hola <strong>{to_name}</strong>,</p>
      <p>Tu código de acceso temporal es:</p>
      <div style="background:#f1f3f5; border-radius:8px; padding:16px 24px; font-size:24px;
                  letter-spacing:3px; font-family:monospace; text-align:center; margin:16px 0;">
        {otp_token}
      </div>
      <p>Este código puede usarse <strong>{settings.otp_max_uses} veces</strong>
         y expira en <strong>{settings.otp_expire_days} días</strong>.</p>
      <p style="color:#868e96; font-size:12px;">
        Si no solicitaste este código, ignora este mensaje.
      </p>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from or settings.smtp_user
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            use_tls=False,
            start_tls=settings.smtp_tls,
        )
        return True
    except Exception as exc:
        logger.error("Failed to send OTP email to %s: %s", to_email, exc)
        return False
