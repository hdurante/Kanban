#!/usr/bin/env python
# =============================================================================
# Project     : Kanban — Tablero Kanban Open-Source
# File        : scripts/create_admin.py
# Description : CLI utility to create or reset the admin user interactively.
#               Useful for initial setup or credential recovery outside Docker.
#               Run with: python scripts/create_admin.py
# -----------------------------------------------------------------------------
# Author      : Hector Manuel Durante Nuñez
# Email       : hector_durante@yahoo.com.mx
# GitHub      : https://github.com/hdurante/Kanban
# License     : MIT — See LICENSE file for details
# Created     : 2026-04-24
# Version     : 1.0.0
# =============================================================================
"""
scripts/create_admin.py
-----------------------
One-time script to create or reset the admin user.
Run with: python scripts/create_admin.py

The app auto-seeds a default admin on first boot, but this script
is useful when you need to reset credentials outside of Docker.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import AsyncSessionLocal, Base, engine
from app.models.user import User, UserRole
from app.services.auth import hash_password
from sqlalchemy.future import select


async def main():
    print("=== Kanban — Admin Setup ===\n")

    email = input("Admin email [admin@kanban.local]: ").strip() or "admin@kanban.local"
    name = input("Admin name  [Administrador]: ").strip() or "Administrador"
    password = input("Admin password (min 8 chars): ").strip()
    if len(password) < 8:
        print("Password too short. Aborting.")
        sys.exit(1)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user:
            user.name = name
            user.password_hash = hash_password(password)
            user.role = UserRole.admin
            user.is_active = True
            print(f"\nUpdated existing user: {email}")
        else:
            user = User(
                name=name,
                email=email,
                password_hash=hash_password(password),
                role=UserRole.admin,
                is_active=True,
            )
            db.add(user)
            print(f"\nCreated new admin user: {email}")

        await db.commit()

    print("Done! You can now log in.\n")


if __name__ == "__main__":
    asyncio.run(main())
