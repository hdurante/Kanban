# =============================================================================
# Project     : Kanban — Tablero Kanban Open-Source
# File        : app/services/auth.py
# Description : Authentication services: bcrypt password hashing/verification,
#               JWT access token creation/decoding, OTP generation and
#               validation, and user credential authentication.
# -----------------------------------------------------------------------------
# Author      : Hector Manuel Durante Nuñez
# Email       : hector_durante@yahoo.com.mx
# GitHub      : https://github.com/hdurante/Kanban
# License     : GNU AGPLv3 — See LICENSE file for details
# Created     : 2026-04-24
# Version     : 1.0.0
# =============================================================================
import secrets
import string
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import settings
from app.models.user import OTPToken, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password helpers ────────────────────────────────────────────────────────


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT helpers ─────────────────────────────────────────────────────────────


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None


# ── OTP helpers ─────────────────────────────────────────────────────────────


def generate_otp(length: int | None = None) -> str:
    length = length or settings.otp_length
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


async def create_otp_token(
    db: AsyncSession,
    user: User,
    max_uses: int | None = None,
    expire_days: int | None = None,
) -> str:
    """Generate a plain OTP, store its hash, return the plain token."""
    plain_token = generate_otp(settings.otp_length)
    token_hash = pwd_context.hash(plain_token)

    otp = OTPToken(
        user_id=user.id,
        token_hash=token_hash,
        max_uses=max_uses or settings.otp_max_uses,
        uses_count=0,
        expires_at=datetime.now(timezone.utc) + timedelta(days=expire_days or settings.otp_expire_days),
    )
    db.add(otp)
    await db.commit()
    return plain_token


async def validate_otp_token(
    db: AsyncSession, email: str, plain_token: str
) -> User | None:
    """Validate an OTP. Returns the User if valid, None otherwise."""
    result = await db.execute(select(User).where(User.email == email, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        return None

    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(OTPToken).where(
            OTPToken.user_id == user.id,
            OTPToken.expires_at > now,
        )
    )
    tokens = result.scalars().all()

    for otp in tokens:
        if otp.uses_count >= otp.max_uses:
            continue
        if pwd_context.verify(plain_token, otp.token_hash):
            otp.uses_count += 1
            await db.commit()
            return user

    return None


# ── User authentication ─────────────────────────────────────────────────────


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    result = await db.execute(
        select(User).where(User.email == email, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if not user or not user.password_hash:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
