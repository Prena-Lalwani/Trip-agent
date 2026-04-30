from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.core.config  # noqa: F401 — sets LangSmith env vars on import
from app.api.routes import admin, auth, chat, trips, ws_trips
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="AI Travel Planner",
    description="Multi-agent travel planning with LangGraph + Gemini",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(admin.router)
app.include_router(trips.router)
app.include_router(ws_trips.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
