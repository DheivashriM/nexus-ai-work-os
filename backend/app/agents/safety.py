from typing import Dict, Any
from app.models.user import User
from app.services.permission_service import PermissionService

class SafetyChecker:
    @staticmethod
    def classify_risk(tool_name: str) -> str:
        read_tools = [
            "get_projects", "get_project", "get_tasks", "get_task",
            "get_user", "get_user_tasks", "get_blockers", "get_user_activity"
        ]
        high_risk_tools = ["delete_project", "delete_task", "bulk_delete"]

        if tool_name in read_tools:
            return "LOW_RISK"
        if tool_name in high_risk_tools:
            return "HIGH_RISK"
        return "NORMAL_WRITE"

    @staticmethod
    def is_authorized(tool_name: str, args: Dict[str, Any], user: User) -> bool:
        """
        Enforce RBAC rules before tool execution.
        """
        if tool_name in ["create_task", "assign_task", "change_task_status", "create_blocker", "resolve_blocker"]:
            return PermissionService.can_create_task(user)
        if tool_name in ["create_project", "delete_project"]:
            return PermissionService.can_create_project(user)
        return True
