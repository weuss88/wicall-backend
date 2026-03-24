from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from core.database import get_db
from core.security import get_current_user, require_manager
from models.models import Lead, User, Campaign

router = APIRouter()

class LeadCreate(BaseModel):
    campaign_id: int
    civilite: Optional[str] = None
    nom_prospect: Optional[str] = None
    prenom: Optional[str] = None
    adresse: Optional[str] = None
    cp: Optional[str] = None
    ville: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    date_rappel: Optional[str] = None
    heure_rappel: Optional[str] = None
    commentaire: Optional[str] = None

class LeadUpdate(BaseModel):
    civilite: Optional[str] = None
    nom_prospect: Optional[str] = None
    prenom: Optional[str] = None
    adresse: Optional[str] = None
    cp: Optional[str] = None
    ville: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    date_rappel: Optional[str] = None
    heure_rappel: Optional[str] = None
    commentaire: Optional[str] = None
    statut: Optional[str] = None

class LeadOut(BaseModel):
    id: int
    campaign_id: int
    campaign_nom: str
    campaign_tag: str
    campaign_client: str
    conseiller_id: int
    conseiller_name: str
    civilite: Optional[str]
    nom_prospect: Optional[str]
    prenom: Optional[str]
    adresse: Optional[str]
    cp: Optional[str]
    ville: Optional[str]
    telephone: Optional[str]
    email: Optional[str]
    date_rappel: Optional[str]
    heure_rappel: Optional[str]
    commentaire: Optional[str]
    statut: Optional[str]
    created_at: datetime
    class Config: from_attributes = True

async def _enrich(lead: Lead, db: AsyncSession) -> dict:
    camp = (await db.execute(select(Campaign).where(Campaign.id == lead.campaign_id))).scalar_one_or_none()
    user = (await db.execute(select(User).where(User.id == lead.conseiller_id))).scalar_one_or_none()
    return {
        "id": lead.id,
        "campaign_id": lead.campaign_id,
        "campaign_nom": camp.nom if camp else "?",
        "campaign_tag": camp.tag if camp else "?",
        "campaign_client": camp.client if camp else "?",
        "conseiller_id": lead.conseiller_id,
        "conseiller_name": (user.full_name or user.username) if user else "?",
        "civilite": lead.civilite,
        "nom_prospect": lead.nom_prospect,
        "prenom": lead.prenom,
        "adresse": lead.adresse,
        "cp": lead.cp,
        "ville": lead.ville,
        "telephone": lead.telephone,
        "email": lead.email,
        "date_rappel": lead.date_rappel,
        "heure_rappel": lead.heure_rappel,
        "commentaire": lead.commentaire,
        "statut": lead.statut or "en_attente",
        "created_at": lead.created_at,
    }

# Conseiller : soumettre un lead
@router.post("/", response_model=LeadOut)
async def create_lead(data: LeadCreate, db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    camp = (await db.execute(select(Campaign).where(Campaign.id == data.campaign_id))).scalar_one_or_none()
    if not camp:
        raise HTTPException(status_code=404, detail="Campagne introuvable")
    lead = Lead(
        conseiller_id=current_user.id,
        campaign_id=data.campaign_id,
        civilite=data.civilite,
        nom_prospect=data.nom_prospect,
        prenom=data.prenom,
        adresse=data.adresse,
        cp=data.cp,
        ville=data.ville,
        telephone=data.telephone,
        email=data.email,
        date_rappel=data.date_rappel,
        heure_rappel=data.heure_rappel,
        commentaire=data.commentaire,
    )
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    return await _enrich(lead, db)

# Manager : tous les leads
@router.get("/", response_model=List[LeadOut])
async def get_all_leads(db: AsyncSession = Depends(get_db),
                        _: User = Depends(require_manager)):
    leads = (await db.execute(select(Lead).order_by(Lead.created_at.desc()))).scalars().all()
    return [await _enrich(l, db) for l in leads]

# Conseiller : ses propres leads
@router.get("/me", response_model=List[LeadOut])
async def get_my_leads(db: AsyncSession = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    leads = (await db.execute(
        select(Lead).where(Lead.conseiller_id == current_user.id).order_by(Lead.created_at.desc())
    )).scalars().all()
    return [await _enrich(l, db) for l in leads]

# Manager : modifier un lead (champs + statut)
@router.put("/{lead_id}", response_model=LeadOut)
async def update_lead(lead_id: int, data: LeadUpdate, db: AsyncSession = Depends(get_db),
                      _: User = Depends(require_manager)):
    lead = (await db.execute(select(Lead).where(Lead.id == lead_id))).scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead introuvable")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(lead, field, value)
    await db.commit()
    await db.refresh(lead)
    return await _enrich(lead, db)

# Stats leads pour un conseiller (compteur)
@router.get("/me/count")
async def get_my_leads_count(db: AsyncSession = Depends(get_db),
                             current_user: User = Depends(get_current_user)):
    leads = (await db.execute(
        select(Lead).where(Lead.conseiller_id == current_user.id)
    )).scalars().all()
    return {"count": len(leads)}
