from __future__ import annotations
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .core.config import settings
from .core.database import engine, init_db, SessionLocal
from .api import health, blocks, cameras, incidents, alerts, simulator, reports, detection

app = FastAPI(title="Smart Campus Shield", version="0.1.0")

# CORS (allow all for demo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create DB tables on startup
@app.on_event("startup")
async def on_startup():
    init_db()
    # Seed demo data if empty
    from .services import seed
    with SessionLocal() as db:
        seed.seed_demo_data(db)

# Include routers
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(blocks.router, prefix="/api/blocks", tags=["blocks"])
app.include_router(cameras.router, prefix="/api/cameras", tags=["cameras"])
app.include_router(incidents.router, prefix="/api/incidents", tags=["incidents"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(simulator.router, prefix="/api/simulator", tags=["simulator"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(detection.router, prefix="/api/detection", tags=["detection"])

# Simple dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# WebSocket manager for incident updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/incidents")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Endpoint to push updates (used internally)
@app.post("/internal/incident_update")
async def incident_update(event: dict, background_tasks: BackgroundTasks):
    # In a real app you would secure this endpoint
    background_tasks.add_task(manager.broadcast, event)
    return {"detail": "broadcast scheduled"}
