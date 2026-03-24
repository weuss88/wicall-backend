from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List, Any
from core.database import get_db
from core.security import get_current_user, require_manager
from models.models import Campaign, User

router = APIRouter()

class CampaignCreate(BaseModel):
    nom: str
    client: str
    tag: str
    cpl: Optional[str] = None
    cp: Any = "national"
    logement: Optional[List[str]] = None
    statut: Optional[List[str]] = None
    chauffage: Optional[List[str]] = None
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    criteres_custom: Optional[List[dict]] = []
    alerte: Optional[str] = None
    actif: bool = True
    taux_devaluation: Optional[int] = 100

class CampaignOut(CampaignCreate):
    id: int
    class Config: from_attributes = True

# Conseiller : lire les campagnes actives
@router.get("/", response_model=List[CampaignOut])
async def get_campaigns(db: AsyncSession = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    # Manager voit tout, conseiller voit uniquement les actives
    if current_user.role == "manager":
        result = await db.execute(select(Campaign).order_by(Campaign.client))
    else:
        result = await db.execute(select(Campaign).where(Campaign.actif == True).order_by(Campaign.client))
    return result.scalars().all()

# Manager : créer
@router.post("/", response_model=CampaignOut)
async def create_campaign(data: CampaignCreate, db: AsyncSession = Depends(get_db),
                          _: User = Depends(require_manager)):
    camp = Campaign(**data.dict())
    db.add(camp)
    await db.commit()
    await db.refresh(camp)
    return camp

# Manager : modifier
@router.put("/{camp_id}", response_model=CampaignOut)
async def update_campaign(camp_id: int, data: CampaignCreate,
                          db: AsyncSession = Depends(get_db),
                          _: User = Depends(require_manager)):
    result = await db.execute(select(Campaign).where(Campaign.id == camp_id))
    camp = result.scalar_one_or_none()
    if not camp:
        raise HTTPException(status_code=404, detail="Campagne introuvable")
    for k, v in data.dict().items():
        setattr(camp, k, v)
    await db.commit()
    await db.refresh(camp)
    return camp

# Manager : toggle actif
@router.patch("/{camp_id}/toggle")
async def toggle_campaign(camp_id: int, db: AsyncSession = Depends(get_db),
                          _: User = Depends(require_manager)):
    result = await db.execute(select(Campaign).where(Campaign.id == camp_id))
    camp = result.scalar_one_or_none()
    if not camp:
        raise HTTPException(status_code=404, detail="Campagne introuvable")
    camp.actif = not camp.actif
    await db.commit()
    return {"id": camp_id, "actif": camp.actif}

# Manager : supprimer
@router.delete("/{camp_id}")
async def delete_campaign(camp_id: int, db: AsyncSession = Depends(get_db),
                          _: User = Depends(require_manager)):
    result = await db.execute(select(Campaign).where(Campaign.id == camp_id))
    camp = result.scalar_one_or_none()
    if not camp:
        raise HTTPException(status_code=404, detail="Campagne introuvable")
    await db.delete(camp)
    await db.commit()
    return {"deleted": camp_id}
