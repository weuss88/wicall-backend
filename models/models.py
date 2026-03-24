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

class Campaign(Base):
    __tablename__ = "campaigns"
    id               = Column(Integer, primary_key=True, index=True)
    nom              = Column(String(100), nullable=False)
    client           = Column(String(100), nullable=False)
    tag              = Column(String(20), nullable=False)
    cpl              = Column(String(20))
    cp               = Column(JSON, default="national")
    logement         = Column(JSON, nullable=True)
    statut           = Column(JSON, nullable=True)
    chauffage        = Column(JSON, nullable=True)
    age_min          = Column(Integer, nullable=True)
    age_max          = Column(Integer, nullable=True)
    criteres_custom  = Column(JSON, default=list)
    alerte           = Column(Text, nullable=True)
    actif            = Column(Boolean, default=True)
    taux_devaluation = Column(Integer, default=100)
    created_at       = Column(DateTime, server_default=func.now())
    updated_at       = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Lead(Base):
    __tablename__ = "leads"
    id              = Column(Integer, primary_key=True, index=True)
    conseiller_id   = Column(Integer, ForeignKey("users.id"), nullable=False)
    campaign_id     = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    civilite        = Column(String(10), nullable=True)
    nom_prospect    = Column(String(100), nullable=True)
    prenom          = Column(String(50), nullable=True)
    adresse         = Column(String(200), nullable=True)
    cp              = Column(String(10), nullable=True)
    ville           = Column(String(100), nullable=True)
    telephone       = Column(String(20), nullable=True)
    email           = Column(String(150), nullable=True)
    date_rappel     = Column(String(10), nullable=True)
    heure_rappel    = Column(String(5), nullable=True)
    commentaire     = Column(Text, nullable=True)
    statut          = Column(String(20), default='en_attente', server_default='en_attente')
    created_at      = Column(DateTime, server_default=func.now())
