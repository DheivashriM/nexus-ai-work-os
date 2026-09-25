from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.project import Project, ProjectMember
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectMemberCreate
from app.repositories.project_repository import ProjectRepository
from app.repositories.user_repository import UserRepository
from app.services.activity_service import ActivityService
from app.services.permission_service import PermissionService

class ProjectService:
    def __init__(self, db: Session):
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.user_repo = UserRepository(db)
        self.activity_service = ActivityService(db)

    def create_project(self, project_in: ProjectCreate, current_user) -> Project:
        PermissionService.enforce_create_project(current_user)
        owner = self.user_repo.get_by_id(project_in.owner_id)
        if not owner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project owner '{project_in.owner_id}' not found."
            )
        project = Project(
            name=project_in.name,
            description=project_in.description,
            status=project_in.status,
            priority=project_in.priority,
            owner_id=project_in.owner_id,
            start_date=project_in.start_date,
            due_date=project_in.due_date
        )
        created_project = self.project_repo.create(project)
        
        # Add owner as project member
        member = ProjectMember(
            project_id=created_project.id,
            user_id=owner.id,
            role="OWNER"
        )
        self.project_repo.add_member(member)

        self.activity_service.log_activity(
            activity_type="PROJECT_CREATED",
            description=f"Created project '{project.name}'",
            user_id=current_user.id,
            project_id=created_project.id,
            metadata={"project_id": created_project.id, "name": project.name}
        )
        return created_project

    def get_project_by_id(self, project_id: str) -> Project:
        project = self.project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{project_id}' not found."
            )
        return project

    def get_all_projects(self, skip: int = 0, limit: int = 100, status_filter: Optional[str] = None) -> List[Project]:
        return self.project_repo.get_all(skip=skip, limit=limit, status=status_filter)

    def update_project(self, project_id: str, project_in: ProjectUpdate, current_user) -> Project:
        project = self.get_project_by_id(project_id)
        if not PermissionService.can_edit_project(current_user, project.owner_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: You cannot edit this project."
            )
        if project_in.name is not None:
            project.name = project_in.name
        if project_in.description is not None:
            project.description = project_in.description
        if project_in.status is not None:
            project.status = project_in.status
        if project_in.priority is not None:
            project.priority = project_in.priority
        if project_in.owner_id is not None:
            owner = self.user_repo.get_by_id(project_in.owner_id)
            if not owner:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User '{project_in.owner_id}' not found.")
            project.owner_id = project_in.owner_id
        if project_in.start_date is not None:
            project.start_date = project_in.start_date
        if project_in.due_date is not None:
            project.due_date = project_in.due_date

        updated_project = self.project_repo.update(project)
        self.activity_service.log_activity(
            activity_type="PROJECT_UPDATED",
            description=f"Updated project '{project.name}'",
            user_id=current_user.id,
            project_id=project.id
        )
        return updated_project

    def add_member(self, project_id: str, member_in: ProjectMemberCreate, current_user) -> ProjectMember:
        project = self.get_project_by_id(project_id)
        user = self.user_repo.get_by_id(member_in.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{member_in.user_id}' not found."
            )
        existing = self.project_repo.get_member(project_id, member_in.user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User '{user.name}' is already a member of project '{project.name}'."
            )
        member = ProjectMember(
            project_id=project_id,
            user_id=member_in.user_id,
            role=member_in.role
        )
        added_member = self.project_repo.add_member(member)
        self.activity_service.log_activity(
            activity_type="PROJECT_MEMBER_ADDED",
            description=f"Added {user.name} to project '{project.name}'",
            user_id=current_user.id,
            project_id=project_id,
            metadata={"user_id": user.id}
        )
        return added_member

    def get_members(self, project_id: str) -> List[ProjectMember]:
        self.get_project_by_id(project_id)
        return self.project_repo.get_members(project_id)
