from sqlalchemy import Column, Integer, String, Boolean, JSON, Text, DateTime, func, ForeignKey
from core.database import Base

class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True, index=True)
    username      = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    full_name     = Column(String(100))
    role          = Column(String(20), default="conseiller")  # manager | conseiller
    is_active     = Column(Boolean, default=True)
    is_owner      = Column(Boolean, default=False)
    pages_access  = Column(JSON, nullable=True)   # null = accès par défaut selon rôle
    created_at    = Column(DateTime, server_default=func.now())
