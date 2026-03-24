from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from core.database import get_db
from core.security import require_manager, hash_password
from models.models import User

router = APIRouter()

class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    is_active: bool
    is_owner: bool = False
    pages_access: Optional[list] = None
    class Config: from_attributes = True

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    role: Optional[str] = None
    pages_access: Optional[list] = None

@router.get("/", response_model=List[UserOut])
async def list_users(db: AsyncSession = Depends(get_db), _: User = Depends(require_manager)):
    result = await db.execute(select(User))
    return result.scalars().all()

@router.put("/{user_id}", response_model=UserOut)
async def update_user(user_id: int, data: UserUpdate,
                      db: AsyncSession = Depends(get_db), _: User = Depends(require_manager)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.password:
        user.hashed_password = hash_password(data.password)
    if data.role is not None:
        user.role = data.role
    if data.pages_access is not None:
        user.pages_access = data.pages_access
    await db.commit()
    await db.refresh(user)
    return user

@router.delete("/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(require_manager)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    await db.delete(user)
    await db.commit()
    return {"deleted": user_id}
