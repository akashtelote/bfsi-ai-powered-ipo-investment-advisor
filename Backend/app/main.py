from dotenv import load_dotenv
load_dotenv()          # loads backend/.env (or project-root .env) before anything else

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import init_db
from app.api import ipos, dashboard, recommendations, live


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="AI-Powered IPO Advisor API",
    description="BFSI Hackathon — ML-driven IPO analysis and recommendations",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:3001", "http://127.0.0.1:3001",
        "http://localhost:3002", "http://127.0.0.1:3002",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ipos.router)
app.include_router(dashboard.router)
app.include_router(recommendations.router)
app.include_router(live.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ipo-advisor-api"}
