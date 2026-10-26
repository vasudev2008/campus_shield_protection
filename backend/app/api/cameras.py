from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..schemas.models import CameraCreate, CameraRead
from ..core.database import get_db
from ..models import Camera, CampusBlock

router = APIRouter()

@router.get("/", response_model=List[CameraRead])
def list_cameras(db: Session = Depends(get_db)):
    return db.query(Camera).all()

@router.post("/", response_model=CameraRead)
def create_camera(camera: CameraCreate, db: Session = Depends(get_db)):
    # Verify block exists
    block = db.query(CampusBlock).filter(CampusBlock.id == camera.block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="Campus block not found")
    db_camera = Camera(
        name=camera.name,
        block_id=camera.block_id,
        is_available=camera.is_available,
        processing_status=camera.processing_status,
    )
    db.add(db_camera)
    db.commit()
    db.refresh(db_camera)
    return db_camera

@router.get("/{camera_id}", response_model=CameraRead)
def get_camera(camera_id: int, db: Session = Depends(get_db)):
    cam = db.query(Camera).filter(Camera.id == camera_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    return cam
