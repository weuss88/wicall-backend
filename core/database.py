from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from core.config import settings

url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://").replace("postgres://", "postgresql+asyncpg://")

engine = create_async_engine(
    url,
    echo=False,
    connect_args={"statement_cache_size": 0}
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Migrations incrementales
        for col_sql in [
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS civilite VARCHAR(10)",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS prenom VARCHAR(50)",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS adresse VARCHAR(200)",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS ville VARCHAR(100)",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS email VARCHAR(150)",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS date_rappel VARCHAR(10)",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS heure_rappel VARCHAR(5)",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS statut VARCHAR(20) DEFAULT 'en_attente'",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_owner BOOLEAN DEFAULT FALSE",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS pages_access JSONB",
            "ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS taux_devaluation INTEGER DEFAULT 100",
        ]:
            await conn.execute(text(col_sql))
        # S'assurer que manager1 est toujours owner
        await conn.execute(text(
            "UPDATE users SET is_owner = TRUE WHERE username = 'manager1'"
        ))

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
