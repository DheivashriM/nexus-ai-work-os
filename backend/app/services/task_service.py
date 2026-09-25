from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.task import Task, TaskComment
from app.schemas.task import TaskCreate, TaskUpdate, TaskCommentCreate
from app.repositories.task_repository import TaskRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.user_repository import UserRepository
from app.services.activity_service import ActivityService
from app.services.notification_service import NotificationService
from app.services.permission_service import PermissionService

class TaskService:
    def __init__(self, db: Session):
        self.db = db
        self.task_repo = TaskRepository(db)
        self.project_repo = ProjectRepository(db)
        self.user_repo = UserRepository(db)
        self.activity_service = ActivityService(db)
        self.notification_service = NotificationService(db)

    def create_task(self, task_in: TaskCreate, current_user) -> Task:
        if not PermissionService.can_create_task(current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to create task.")

        project = self.project_repo.get_by_id(task_in.project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{task_in.project_id}' not found.")

        assignee = None
        if task_in.assignee_id:
            assignee = self.user_repo.get_by_id(task_in.assignee_id)
            if not assignee:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Assignee user '{task_in.assignee_id}' not found.")

        task = Task(
            project_id=task_in.project_id,
            title=task_in.title,
            description=task_in.description,
            status=task_in.status,
            priority=task_in.priority,
            assignee_id=task_in.assignee_id,
            created_by=current_user.id,
            due_date=task_in.due_date
        )
        created_task = self.task_repo.create(task)

        # Audit log
        self.activity_service.log_activity(
            activity_type="TASK_CREATED",
            description=f"Created task '{task.title}' in project '{project.name}'",
            user_id=current_user.id,
            project_id=project.id,
            task_id=created_task.id,
            metadata={"title": task.title, "assignee_id": task.assignee_id}
        )

        # Internal Notification if assigned
        if assignee and assignee.id != current_user.id:
            self.notification_service.create_notification(
                user_id=assignee.id,
                type="TASK_ASSIGNED",
                title="New Task Assigned",
                message=f"You were assigned to task '{task.title}' in '{project.name}'"
            )

        return created_task

    def get_task_by_id(self, task_id: str) -> Task:
        task = self.task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task '{task_id}' not found.")
        return task

    def get_all_tasks(
        self,
        skip: int = 0,
        limit: int = 100,
        project_id: Optional[str] = None,
        assignee_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[Task]:
        return self.task_repo.get_all(
            skip=skip,
            limit=limit,
            project_id=project_id,
            assignee_id=assignee_id,
            status=status_filter,
            priority=priority
        )

    def update_task(self, task_id: str, task_in: TaskUpdate, current_user) -> Task:
        task = self.get_task_by_id(task_id)
        if not PermissionService.can_update_task(current_user, task.assignee_id, task.created_by):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to update task.")

        old_status = task.status
        old_assignee = task.assignee_id

        if task_in.title is not None:
            task.title = task_in.title
        if task_in.description is not None:
            task.description = task_in.description
        if task_in.status is not None:
            valid_statuses = ["TODO", "IN_PROGRESS", "IN_REVIEW", "COMPLETED", "BLOCKED"]
            if task_in.status not in valid_statuses:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid task status '{task_in.status}'.")
            task.status = task_in.status
        if task_in.priority is not None:
            valid_priorities = ["LOW", "MEDIUM", "HIGH", "URGENT"]
            if task_in.priority not in valid_priorities:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid task priority '{task_in.priority}'.")
            task.priority = task_in.priority
        if task_in.due_date is not None:
            task.due_date = task_in.due_date

        if task_in.assignee_id is not None and task_in.assignee_id != old_assignee:
            if task_in.assignee_id != "":
                assignee = self.user_repo.get_by_id(task_in.assignee_id)
                if not assignee:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User '{task_in.assignee_id}' not found.")
                task.assignee_id = task_in.assignee_id
            else:
                task.assignee_id = None

        updated_task = self.task_repo.update(task)

        # Audit activity logging
        if task_in.status and task_in.status != old_status:
            self.activity_service.log_activity(
                activity_type="TASK_STATUS_CHANGED",
                description=f"Task '{task.title}' status changed from {old_status} to {task.status}",
                user_id=current_user.id,
                project_id=task.project_id,
                task_id=task.id,
                metadata={"old_status": old_status, "new_status": task.status}
            )

        if task_in.assignee_id is not None and task_in.assignee_id != old_assignee:
            assignee_name = updated_task.assignee.name if updated_task.assignee else "Unassigned"
            self.activity_service.log_activity(
                activity_type="TASK_ASSIGNED",
                description=f"Assigned task '{task.title}' to {assignee_name}",
                user_id=current_user.id,
                project_id=task.project_id,
                task_id=task.id,
                metadata={"assignee_id": task.assignee_id}
            )
            if updated_task.assignee_id and updated_task.assignee_id != current_user.id:
                self.notification_service.create_notification(
                    user_id=updated_task.assignee_id,
                    type="TASK_ASSIGNED",
                    title="Task Assigned",
                    message=f"Task '{task.title}' has been assigned to you."
                )

        return updated_task

    def assign_task(self, task_id: str, assignee_id: Optional[str], current_user) -> Task:
        return self.update_task(task_id, TaskUpdate(assignee_id=assignee_id or ""), current_user)

    def delete_task(self, task_id: str, current_user) -> None:
        task = self.get_task_by_id(task_id)
        if not PermissionService.can_create_project(current_user) and task.created_by != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to delete task.")
        self.task_repo.delete(task)
        self.activity_service.log_activity(
            activity_type="TASK_DELETED",
            description=f"Deleted task '{task.title}'",
            user_id=current_user.id,
            project_id=task.project_id
        )

    def add_comment(self, task_id: str, comment_in: TaskCommentCreate, current_user) -> TaskComment:
        task = self.get_task_by_id(task_id)
        comment = TaskComment(
            task_id=task_id,
            user_id=current_user.id,
            content=comment_in.content
        )
        added_comment = self.task_repo.add_comment(comment)

        self.activity_service.log_activity(
            activity_type="TASK_COMMENT_ADDED",
            description=f"Added comment on task '{task.title}'",
            user_id=current_user.id,
            project_id=task.project_id,
            task_id=task.id
        )

        if task.assignee_id and task.assignee_id != current_user.id:
            self.notification_service.create_notification(
                user_id=task.assignee_id,
                type="COMMENT_ADDED",
                title="New Comment on Task",
                message=f"{current_user.name} commented on '{task.title}'"
            )

        return added_comment
