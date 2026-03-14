"""
Script à lancer UNE SEULE FOIS pour créer le compte manager initial.
Usage : python seed.py
"""
import asyncio
from core.database import init_db, AsyncSessionLocal
from core.security import hash_password
from models.models import User

async def seed():
    await init_db()
    async with AsyncSessionLocal() as db:
        manager = User(
            username="manager1",
            hashed_password=hash_password("manager123"),
            full_name="Manager WiCall",
            role="manager",
            is_active=True
        )
        db.add(manager)

        conseiller1 = User(
            username="conseiller1",
            hashed_password=hash_password("conseil123"),
            full_name="Marie Dupont",
            role="conseiller",
            is_active=True
        )
        db.add(conseiller1)

        conseiller2 = User(
            username="conseiller2",
            hashed_password=hash_password("conseil456"),
            full_name="Pierre Martin",
            role="conseiller",
            is_active=True
        )
        db.add(conseiller2)

        await db.commit()
        print("✅ Comptes créés : manager1 / conseiller1 / conseiller2")

if __name__ == "__main__":
    asyncio.run(seed())
