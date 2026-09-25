from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.team import TeamCreate, TeamRead, TeamUpdate, TeamMemberCreate, TeamMemberRead
from app.services.team_service import TeamService

router = APIRouter(prefix="/teams", tags=["Teams"])

@router.get("", response_model=List[TeamRead])
def get_teams(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    service = TeamService(db)
    return service.get_all_teams(skip=skip, limit=limit)

@router.post("", response_model=TeamRead, status_code=status.HTTP_201_CREATED)
def create_team(team_in: TeamCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = TeamService(db)
    return service.create_team(team_in, current_user.id)

@router.get("/{team_id}", response_model=TeamRead)
def get_team_by_id(team_id: str, db: Session = Depends(get_db)):
    service = TeamService(db)
    return service.get_team_by_id(team_id)

@router.put("/{team_id}", response_model=TeamRead)
def update_team(team_id: str, team_in: TeamUpdate, db: Session = Depends(get_db)):
    service = TeamService(db)
    return service.update_team(team_id, team_in)

@router.post("/{team_id}/members", response_model=TeamMemberRead, status_code=status.HTTP_201_CREATED)
def add_team_member(team_id: str, member_in: TeamMemberCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = TeamService(db)
    return service.add_member(team_id, member_in, current_user.id)
