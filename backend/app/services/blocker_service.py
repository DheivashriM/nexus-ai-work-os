from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.blocker import Blocker
from app.schemas.blocker import BlockerCreate, BlockerUpdate
from app.repositories.blocker_repository import BlockerRepository
from app.repositories.task_repository import TaskRepository
from app.services.activity_service import ActivityService
from app.services.notification_service import NotificationService

class BlockerService:
    def __init__(self, db: Session):
        self.db = db
        self.blocker_repo = BlockerRepository(db)
        self.task_repo = TaskRepository(db)
        self.activity_service = ActivityService(db)
        self.notification_service = NotificationService(db)

    def create_blocker(self, blocker_in: BlockerCreate, current_user) -> Blocker:
        task = self.task_repo.get_by_id(blocker_in.task_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task '{blocker_in.task_id}' not found.")

        blocker = Blocker(
            task_id=blocker_in.task_id,
            reported_by=current_user.id,
            description=blocker_in.description,
            severity=blocker_in.severity,
            status="OPEN"
        )
        created_blocker = self.blocker_repo.create(blocker)

        # Automatically mark task status as BLOCKED
        task.status = "BLOCKED"
        self.task_repo.update(task)

        # Audit log
        self.activity_service.log_activity(
            activity_type="BLOCKER_CREATED",
            description=f"Reported blocker on task '{task.title}': {blocker_in.description}",
            user_id=current_user.id,
            project_id=task.project_id,
            task_id=task.id,
            metadata={"severity": blocker_in.severity}
        )

        # Notify task assignee or creator
        notify_user_id = task.assignee_id or task.created_by
        if notify_user_id and notify_user_id != current_user.id:
            self.notification_service.create_notification(
                user_id=notify_user_id,
                type="BLOCKER_CREATED",
                title="Task Blocked!",
                message=f"Blocker reported on '{task.title}': {blocker.description}"
            )

        # Dispatch Authenticated n8n Webhook Alert (Emergency WhatsApp/Slack)
        try:
            from app.services.n8n_service import N8nService
            N8nService.dispatch_event_async(
                event_type="BLOCKER_RAISED",
                data={
                    "blocker_id": created_blocker.id,
                    "task_id": task.id,
                    "task_title": task.title,
                    "reported_by": current_user.name,
                    "reporter_email": current_user.email,
                    "severity": created_blocker.severity,
                    "description": created_blocker.description
                }
            )
        except Exception as e:
            print("[BlockerService] n8n dispatch error:", e)

        return created_blocker

    def get_blocker_by_id(self, blocker_id: str) -> Blocker:
        blocker = self.blocker_repo.get_by_id(blocker_id)
        if not blocker:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Blocker '{blocker_id}' not found.")
        return blocker

    def get_all_blockers(
        self,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> List[Blocker]:
        return self.blocker_repo.get_all(skip=skip, limit=limit, status=status_filter, task_id=task_id)

    def update_blocker(self, blocker_id: str, blocker_in: BlockerUpdate, current_user) -> Blocker:
        blocker = self.get_blocker_by_id(blocker_id)
        task = self.task_repo.get_by_id(blocker.task_id)

        if blocker_in.description is not None:
            blocker.description = blocker_in.description
        if blocker_in.severity is not None:
            blocker.severity = blocker_in.severity
        if blocker_in.status is not None:
            old_status = blocker.status
            blocker.status = blocker_in.status
            if blocker_in.status == "RESOLVED" and old_status != "RESOLVED":
                blocker.resolved_at = datetime.now(timezone.utc)
                # Unblock task if no other open blockers
                other_open = [b for b in task.blockers if b.id != blocker.id and b.status == "OPEN"]
                if not other_open and task.status == "BLOCKED":
                    task.status = "IN_PROGRESS"
                    self.task_repo.update(task)

                self.activity_service.log_activity(
                    activity_type="BLOCKER_RESOLVED",
                    description=f"Resolved blocker on task '{task.title}'",
                    user_id=current_user.id,
                    project_id=task.project_id,
                    task_id=task.id
                )

        return self.blocker_repo.update(blocker)
