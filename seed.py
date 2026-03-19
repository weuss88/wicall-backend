import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from passlib.context import CryptContext
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "").replace("postgresql://", "postgresql+asyncpg://").replace("postgres://", "postgresql+asyncpg://")

engine = create_async_engine(DATABASE_URL, echo=True, connect_args={"statement_cache_size": 0})
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def seed():
    from sqlalchemy import text
    async with AsyncSessionLocal() as db:
        for user in [
            ("manager1", "manager123", "Manager WiCall", "manager"),
            ("conseiller1", "conseil123", "Marie Dupont", "conseiller"),
            ("conseiller2", "conseil456", "Pierre Martin", "conseiller"),
        ]:
            hashed = pwd_context.hash(user[1])
            await db.execute(text(
                "INSERT INTO users (username, hashed_password, full_name, role, is_active) "
                "VALUES (:u, :h, :f, :r, true) ON CONFLICT (username) DO UPDATE SET hashed_password=:h"
            ), {"u": user[0], "h": hashed, "f": user[2], "r": user[3]})
        await db.commit()
        print("✅ Comptes créés")

if __name__ == "__main__":
    asyncio.run(seed())
