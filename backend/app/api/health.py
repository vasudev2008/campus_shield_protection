# backend/app/api/health.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/ping", summary="Health check")
async def ping():
    return {"status": "ok"}
