from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete as sql_delete, func, and_
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt as jose_jwt
from core.database import get_db
from core.limiter import limiter
from core.security import verify_password, create_token, hash_password, get_current_user, require_manager
from core.config import settings
from core.audit import log_action
from models.models import User, RevokedToken, AuditLog

router = APIRouter()

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str = ""
    role: str = "conseiller"
    pages_access: Optional[list] = None

class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    is_active: bool
    is_owner: bool = False
    pages_access: Optional[list] = None
    class Config: from_attributes = True

@router.post("/login")
@limiter.limit("5/minute")
async def login(response: Response, request: Request, form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == form.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form.password, user.hashed_password):
        await log_action(db, None, "login_failed", form.username)
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    if not user.is_active:
        await log_action(db, None, "login_failed", form.username)
        raise HTTPException(status_code=403, detail="Compte désactivé")
    token = create_token({"sub": str(user.id), "role": user.role})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )
    await log_action(db, user.id, "login", user.username)
    return {
        "role": user.role,
        "full_name": user.full_name,
        "is_owner": bool(user.is_owner),
        "pages_access": user.pages_access,
    }

@router.post("/logout")
async def logout(response: Response,
                 access_token: str = Cookie(None),
                 current_user: User = Depends(get_current_user),
                 db: AsyncSession = Depends(get_db)):
    if access_token:
        try:
            payload = jose_jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp:
                db.add(RevokedToken(jti=jti, expires_at=datetime.utcfromtimestamp(exp)))
                await db.execute(sql_delete(RevokedToken).where(RevokedToken.expires_at < datetime.utcnow()))
                await db.commit()
        except JWTError:
            pass
    response.delete_cookie(key="access_token", path="/", secure=True, httponly=True, samesite="none")
    await log_action(db, current_user.id, "logout", current_user.username)
    return {"ok": True}

@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/register", response_model=UserOut)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db),
                   current_user: User = Depends(require_manager)):
    if len(data.password) < 5:
        raise HTTPException(status_code=400, detail="Le mot de passe doit contenir au moins 5 caractères")
    existing = await db.execute(select(User).where(User.username == data.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Identifiant déjà utilisé")
    user = User(username=data.username, hashed_password=hash_password(data.password),
                full_name=data.full_name, role=data.role, pages_access=data.pages_access)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    await log_action(db, current_user.id, "user_create", data.username)
    return user

@router.get("/alerts")
async def get_alerts(db: AsyncSession = Depends(get_db), _: User = Depends(require_manager)):
    cutoff = datetime.utcnow() - timedelta(hours=1)
    result = await db.execute(
        select(AuditLog.cible, func.count(AuditLog.id).label('n'))
        .where(and_(AuditLog.action == 'login_failed', AuditLog.created_at >= cutoff))
        .group_by(AuditLog.cible)
        .having(func.count(AuditLog.id) >= 3)
        .order_by(func.count(AuditLog.id).desc())
    )
    rows = result.all()
    return [{"username": r.cible, "count": r.n} for r in rows]
