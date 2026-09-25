from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate, TaskAssignPayload, TaskCommentCreate, TaskCommentRead
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.get("", response_model=List[TaskRead])
def get_tasks(
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[str] = None,
    assignee_id: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = TaskService(db)
    return service.get_all_tasks(
        skip=skip,
        limit=limit,
        project_id=project_id,
        assignee_id=assignee_id,
        status_filter=status_filter,
        priority=priority
    )

@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(task_in: TaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = TaskService(db)
    return service.create_task(task_in, current_user)

@router.get("/{task_id}", response_model=TaskRead)
def get_task_by_id(task_id: str, db: Session = Depends(get_db)):
    service = TaskService(db)
    return service.get_task_by_id(task_id)

@router.put("/{task_id}", response_model=TaskRead)
def update_task(task_id: str, task_in: TaskUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = TaskService(db)
    return service.update_task(task_id, task_in, current_user)

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = TaskService(db)
    service.delete_task(task_id, current_user)

@router.post("/{task_id}/assign", response_model=TaskRead)
def assign_task(task_id: str, payload: TaskAssignPayload, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = TaskService(db)
    return service.assign_task(task_id, payload.assignee_id, current_user)

@router.post("/{task_id}/comments", response_model=TaskCommentRead, status_code=status.HTTP_201_CREATED)
def add_task_comment(task_id: str, comment_in: TaskCommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = TaskService(db)
    return service.add_comment(task_id, comment_in, current_user)
