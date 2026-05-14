from sqlalchemy.ext.asyncio import AsyncSession
from models.models import AuditLog

async def log_action(db: AsyncSession, user_id: int, action: str, cible: str = None, detail: str = None):
    db.add(AuditLog(user_id=user_id, action=action, cible=cible, detail=detail))
    await db.commit()
