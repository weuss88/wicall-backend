from datetime import datetime, timedelta
import uuid
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.config import settings
from core.database import get_db
from models.models import User, RevokedToken

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

async def get_current_user(access_token: str = Cookie(None), db: AsyncSession = Depends(get_db)):
    creds_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide", headers={"WWW-Authenticate": "Bearer"})
    if not access_token:
        raise creds_exception
    try:
        payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        jti: str = payload.get("jti")
        if not user_id:
            raise creds_exception
    except JWTError:
        raise creds_exception
    if jti:
        revoked = await db.execute(select(RevokedToken).where(RevokedToken.jti == jti))
        if revoked.scalar_one_or_none():
            raise creds_exception
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise creds_exception
    return user

def require_manager(current_user: User = Depends(get_current_user)):
    if current_user.role != "manager":
        raise HTTPException(status_code=403, detail="Accès réservé au manager")
    return current_user
