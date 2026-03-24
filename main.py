from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from contextlib import asynccontextmanager
import os

from core.database import init_db
from routes import auth, campaigns, users, leads

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="WiCall API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://wicall-frontend.vercel.app", "http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(campaigns.router, prefix="/campaigns", tags=["Campaigns"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(leads.router, prefix="/leads", tags=["Leads"])

@app.get("/")
async def root():
    return {"status": "WiCall API running", "version": "1.0.0"}
