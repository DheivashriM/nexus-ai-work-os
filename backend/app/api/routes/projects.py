from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate, ProjectMemberCreate, ProjectMemberRead
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.get("", response_model=List[ProjectRead])
def get_projects(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    service = ProjectService(db)
    return service.get_all_projects(skip=skip, limit=limit, status_filter=status_filter)

@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(project_in: ProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = ProjectService(db)
    return service.create_project(project_in, current_user)

@router.get("/{project_id}", response_model=ProjectRead)
def get_project_by_id(project_id: str, db: Session = Depends(get_db)):
    service = ProjectService(db)
    return service.get_project_by_id(project_id)

@router.put("/{project_id}", response_model=ProjectRead)
def update_project(project_id: str, project_in: ProjectUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = ProjectService(db)
    return service.update_project(project_id, project_in, current_user)

@router.get("/{project_id}/members", response_model=List[ProjectMemberRead])
def get_project_members(project_id: str, db: Session = Depends(get_db)):
    service = ProjectService(db)
    return service.get_members(project_id)

@router.post("/{project_id}/members", response_model=ProjectMemberRead, status_code=status.HTTP_201_CREATED)
def add_project_member(project_id: str, member_in: ProjectMemberCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = ProjectService(db)
    return service.add_member(project_id, member_in, current_user)
