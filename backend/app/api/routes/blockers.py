from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.blocker import BlockerCreate, BlockerRead, BlockerUpdate
from app.services.blocker_service import BlockerService

router = APIRouter(prefix="/blockers", tags=["Blockers"])

@router.get("", response_model=List[BlockerRead])
def get_blockers(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = Query(None, alias="status"),
    task_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = BlockerService(db)
    return service.get_all_blockers(skip=skip, limit=limit, status_filter=status_filter, task_id=task_id)

@router.post("", response_model=BlockerRead, status_code=status.HTTP_201_CREATED)
def create_blocker(blocker_in: BlockerCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = BlockerService(db)
    return service.create_blocker(blocker_in, current_user)

@router.get("/{blocker_id}", response_model=BlockerRead)
def get_blocker_by_id(blocker_id: str, db: Session = Depends(get_db)):
    service = BlockerService(db)
    return service.get_blocker_by_id(blocker_id)

@router.put("/{blocker_id}", response_model=BlockerRead)
def update_blocker(blocker_id: str, blocker_in: BlockerUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = BlockerService(db)
    return service.update_blocker(blocker_id, blocker_in, current_user)
