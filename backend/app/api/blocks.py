from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..schemas.models import CampusBlockCreate, CampusBlockRead
from ..core.database import get_db
from ..models import CampusBlock

router = APIRouter()

@router.get("/", response_model=List[CampusBlockRead])
def list_blocks(db: Session = Depends(get_db)):
    return db.query(CampusBlock).all()

@router.post("/", response_model=CampusBlockRead)
def create_block(block: CampusBlockCreate, db: Session = Depends(get_db)):
    db_block = CampusBlock(name=block.name, description=block.description)
    db.add(db_block)
    db.commit()
    db.refresh(db_block)
    return db_block

@router.get("/{block_id}", response_model=CampusBlockRead)
def get_block(block_id: int, db: Session = Depends(get_db)):
    block = db.query(CampusBlock).filter(CampusBlock.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="Campus block not found")
    return block
