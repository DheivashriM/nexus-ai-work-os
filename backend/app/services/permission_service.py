from fastapi import HTTPException, status
from app.models.user import User

class PermissionService:
    @staticmethod
    def can_create_project(user: User) -> bool:
        return user.role in ["ADMIN", "MANAGER"]

    @staticmethod
    def can_edit_project(user: User, owner_id: str) -> bool:
        if user.role == "ADMIN":
            return True
        if user.role == "MANAGER" and user.id == owner_id:
            return True
        return False

    @staticmethod
    def can_create_task(user: User) -> bool:
        return user.role in ["ADMIN", "MANAGER", "MEMBER"]

    @staticmethod
    def can_assign_task(user: User) -> bool:
        return user.role in ["ADMIN", "MANAGER", "MEMBER"]

    @staticmethod
    def can_update_task(user: User, task_assignee_id: str | None, task_creator_id: str) -> bool:
        if user.role in ["ADMIN", "MANAGER"]:
            return True
        if user.id == task_assignee_id or user.id == task_creator_id:
            return True
        return True  # Members can collaborate and update tasks

    @staticmethod
    def can_view_project(user: User) -> bool:
        return True

    @staticmethod
    def can_view_user_activity(user: User) -> bool:
        return True

    @staticmethod
    def enforce_create_project(user: User):
        if not PermissionService.can_create_project(user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: Only ADMIN or MANAGER can create projects."
            )
