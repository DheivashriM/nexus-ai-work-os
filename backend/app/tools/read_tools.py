from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from app.tools.registry import BaseTool, ToolContext, registry
from app.tools.entity_resolver import EntityResolver
from app.services.project_service import ProjectService
from app.services.task_service import TaskService
from app.services.blocker_service import BlockerService
from app.services.user_service import UserService
from app.services.activity_service import ActivityService

# 1. GetProjectsTool
class GetProjectsArgs(BaseModel):
    status: Optional[str] = Field(None, description="Optional project status filter (PLANNING, ACTIVE, ON_HOLD, COMPLETED)")

class GetProjectsTool(BaseTool):
    name = "get_projects"
    description = "Retrieve list of projects with status, priority, owner details, and timestamps."
    category = "PROJECT_TOOLS"
    risk_level = "LOW_RISK"
    args_schema = GetProjectsArgs

    def execute(self, args: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        service = ProjectService(context.db)
        projects = service.get_all_projects(status_filter=args.get("status"))
        return {
            "count": len(projects),
            "projects": [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "status": p.status,
                    "priority": p.priority,
                    "owner": p.owner.name if p.owner else "Unassigned",
                    "due_date": str(p.due_date) if p.due_date else None
                }
                for p in projects
            ]
        }

# 2. GetProjectTool
class GetProjectArgs(BaseModel):
    project_identifier: str = Field(..., description="Project name or project UUID")

class GetProjectTool(BaseTool):
    name = "get_project"
    description = "Get detailed project information including members and task progress by name or ID."
    category = "PROJECT_TOOLS"
    risk_level = "LOW_RISK"
    args_schema = GetProjectArgs

    def execute(self, args: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        project, candidates, err = EntityResolver.resolve_project(context.db, args["project_identifier"])
        if err:
            return {"error": err, "candidates": [p.name for p in candidates] if candidates else []}
        
        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "priority": project.priority,
            "owner": project.owner.name if project.owner else None,
            "tasks_count": len(project.tasks),
            "members": [m.user.name for m in project.members if m.user]
        }

# 3. GetTasksTool
class GetTasksArgs(BaseModel):
    project_identifier: Optional[str] = Field(None, description="Project name or ID filter")
    status: Optional[str] = Field(None, description="Task status filter (TODO, IN_PROGRESS, IN_REVIEW, COMPLETED, BLOCKED)")
    priority: Optional[str] = Field(None, description="Task priority filter (LOW, MEDIUM, HIGH, URGENT)")
    overdue_only: Optional[bool] = Field(False, description="Filter for overdue tasks only")

class GetTasksTool(BaseTool):
    name = "get_tasks"
    description = "Retrieve list of tasks matching filter criteria like project, status, priority, or overdue status."
    category = "TASK_TOOLS"
    risk_level = "LOW_RISK"
    args_schema = GetTasksArgs

    def execute(self, args: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        project_id = None
        if args.get("project_identifier"):
            p, _, _ = EntityResolver.resolve_project(context.db, args["project_identifier"])
            if p:
                project_id = p.id

        service = TaskService(context.db)
        tasks = service.get_all_tasks(
            project_id=project_id,
            status_filter=args.get("status"),
            priority=args.get("priority")
        )

        return {
            "count": len(tasks),
            "tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "status": t.status,
                    "priority": t.priority,
                    "project_name": t.project.name if t.project else None,
                    "assignee": t.assignee.name if t.assignee else "Unassigned",
                    "due_date": str(t.due_date) if t.due_date else None
                }
                for t in tasks
            ]
        }

# 4. SearchTasksTool (NEW SEARCH TOOL)
class SearchTasksArgs(BaseModel):
    query: str = Field(..., description="Search query string for task titles")
    project_identifier: Optional[str] = Field(None, description="Optional project name or UUID to scope search")

class SearchTasksTool(BaseTool):
    name = "search_tasks"
    description = "Search operational tasks by title substring or tokens, scoped by optional project context."
    category = "TASK_TOOLS"
    risk_level = "LOW_RISK"
    args_schema = SearchTasksArgs

    def execute(self, args: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        project_id = None
        project_name = None
        if args.get("project_identifier"):
            p, _, err = EntityResolver.resolve_project(context.db, args["project_identifier"])
            if p:
                project_id = p.id
                project_name = p.name

        task, candidates, err = EntityResolver.resolve_task(context.db, args["query"], project_id=project_id)
        if task:
            return {
                "count": 1,
                "tasks": [{
                    "id": task.id,
                    "title": task.title,
                    "status": task.status,
                    "priority": task.priority,
                    "project": task.project.name if task.project else project_name,
                    "assignee": task.assignee.name if task.assignee else "Unassigned"
                }]
            }
        elif candidates:
            return {
                "count": len(candidates),
                "candidates": [{
                    "id": t.id,
                    "title": t.title,
                    "project": t.project.name if t.project else None,
                    "assignee": t.assignee.name if t.assignee else "Unassigned"
                } for t in candidates]
            }
        return {
            "count": 0,
            "tasks": [],
            "message": f"No existing tasks found matching '{args['query']}'."
        }

# 5. GetTaskTool
class GetTaskArgs(BaseModel):
    task_identifier: str = Field(..., description="Task title or UUID")

class GetTaskTool(BaseTool):
    name = "get_task"
    description = "Get detailed information for a single task including comments and open blockers."
    category = "TASK_TOOLS"
    risk_level = "LOW_RISK"
    args_schema = GetTaskArgs

    def execute(self, args: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        task, candidates, err = EntityResolver.resolve_task(context.db, args["task_identifier"])
        if err:
            return {"error": err}
        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "project_name": task.project.name if task.project else None,
            "assignee": task.assignee.name if task.assignee else "Unassigned",
            "creator": task.creator.name if task.creator else "Unknown",
            "due_date": str(task.due_date) if task.due_date else None,
            "comments": [{"user": c.user.name if c.user else "User", "content": c.content} for c in task.comments],
            "blockers": [{"description": b.description, "severity": b.severity, "status": b.status} for b in task.blockers]
        }

# 6. GetUserTool
class GetUserArgs(BaseModel):
    user_identifier: str = Field(..., description="User name, email, or UUID")

class GetUserTool(BaseTool):
    name = "get_user"
    description = "Get user details and role information."
    category = "TEAM_TOOLS"
    risk_level = "LOW_RISK"
    args_schema = GetUserArgs

    def execute(self, args: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        user, candidates, err = EntityResolver.resolve_user(context.db, args["user_identifier"])
        if err:
            return {"error": err, "candidates": [u.name for u in candidates] if candidates else []}
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "status": user.status
        }

# 7. GetTeamMembersTool
class GetTeamMembersArgs(BaseModel):
    role: Optional[str] = Field(None, description="Optional role filter (ADMIN, MANAGER, MEMBER)")

class GetTeamMembersTool(BaseTool):
    name = "get_team_members"
    description = "Retrieve full organization team roster with roles, emails, and active/completed task counts."
    category = "TEAM_TOOLS"
    risk_level = "LOW_RISK"
    args_schema = GetTeamMembersArgs

    def execute(self, args: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        user_service = UserService(context.db)
        task_service = TaskService(context.db)
        users = user_service.get_all_users()

        if args.get("role"):
            users = [u for u in users if u.role.upper() == args["role"].upper()]

        roster = []
        for u in users:
            u_tasks = task_service.get_all_tasks(assignee_id=u.id)
            active_cnt = len([t for t in u_tasks if t.status != "COMPLETED"])
            completed_cnt = len([t for t in u_tasks if t.status == "COMPLETED"])
            roster.append({
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "role": u.role,
                "status": u.status,
                "active_tasks_count": active_cnt,
                "completed_tasks_count": completed_cnt
            })

        return {
            "count": len(roster),
            "users": roster
        }

# 8. GetTeamWorkloadTool (NEW WORKLOAD TOOL)
class GetTeamWorkloadArgs(BaseModel):
    pass

class GetTeamWorkloadTool(BaseTool):
    name = "get_team_workload"
    description = "Analyze team workload across all members (who has the most tasks, who has no tasks)."
    category = "TEAM_TOOLS"
    risk_level = "LOW_RISK"
    args_schema = GetTeamWorkloadArgs

    def execute(self, args: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        user_service = UserService(context.db)
        task_service = TaskService(context.db)
        users = user_service.get_all_users()

        workloads = []
        for u in users:
            u_tasks = task_service.get_all_tasks(assignee_id=u.id)
            active_tasks = [t for t in u_tasks if t.status != "COMPLETED"]
            workloads.append({
                "name": u.name,
                "role": u.role,
                "active_tasks_count": len(active_tasks),
                "completed_tasks_count": len(u_tasks) - len(active_tasks)
            })

        # Sort by active task count descending
        workloads.sort(key=lambda x: x["active_tasks_count"], reverse=True)
        most_loaded = workloads[0]["name"] if workloads else "None"

        return {
            "total_members": len(workloads),
            "most_loaded_member": most_loaded,
            "workloads": workloads
        }

# 9. GetUserTasksTool
class GetUserTasksArgs(BaseModel):
    user_identifier: str = Field(..., description="User name, email, or UUID")

class GetUserTasksTool(BaseTool):
    name = "get_user_tasks"
    description = "Retrieve all active tasks assigned to a specific team member (e.g. 'What is Sibi working on?')."
    category = "TASK_TOOLS"
    risk_level = "LOW_RISK"
    args_schema = GetUserTasksArgs

    def execute(self, args: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        user, candidates, err = EntityResolver.resolve_user(context.db, args["user_identifier"])
        if err or not user:
            return {"error": f"Could not resolve team member '{args['user_identifier']}': {err or 'User not found'}"}

        service = TaskService(context.db)
        tasks = service.get_all_tasks(assignee_id=user.id)
        return {
            "user": user.name,
            "user_id": user.id,
            "active_tasks_count": len([t for t in tasks if t.status != "COMPLETED"]),
            "tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "status": t.status,
                    "priority": t.priority,
                    "project": t.project.name if t.project else None,
                    "due_date": str(t.due_date) if t.due_date else None
                }
                for t in tasks
            ]
        }

# 10. GetBlockersTool
class GetBlockersArgs(BaseModel):
    status: Optional[str] = Field("OPEN", description="Blocker status (OPEN, RESOLVED, or leave blank for all)")
    user_identifier: Optional[str] = Field(None, description="Optional team member name or ID to filter blockers")

class GetBlockersTool(BaseTool):
    name = "get_blockers"
    description = "Retrieve active or resolved project blockers across tasks."
    category = "BLOCKER_TOOLS"
    risk_level = "LOW_RISK"
    args_schema = GetBlockersArgs

    def execute(self, args: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        service = BlockerService(context.db)
        blockers = service.get_all_blockers(status_filter=args.get("status"))

        if args.get("user_identifier"):
            user, _, err = EntityResolver.resolve_user(context.db, args["user_identifier"])
            if user:
                blockers = [b for b in blockers if b.task and b.task.assignee_id == user.id]

        return {
            "count": len(blockers),
            "blockers": [
                {
                    "id": b.id,
                    "task_title": b.task.title if b.task else None,
                    "task_id": b.task_id,
                    "reported_by": b.reporter.name if b.reporter else None,
                    "description": b.description,
                    "severity": b.severity,
                    "status": b.status,
                    "created_at": str(b.created_at)
                }
                for b in blockers
            ]
        }

# 11. GetUserActivityTool
class GetUserActivityArgs(BaseModel):
    user_identifier: Optional[str] = Field(None, description="Optional user name or ID to filter activities")

class GetUserActivityTool(BaseTool):
    name = "get_user_activity"
    description = "Retrieve recent audit activity logs for a user or project."
    category = "AUDIT_TOOLS"
    risk_level = "LOW_RISK"
    args_schema = GetUserActivityArgs

    def execute(self, args: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        user_id = None
        if args.get("user_identifier"):
            u, _, _ = EntityResolver.resolve_user(context.db, args["user_identifier"])
            if u:
                user_id = u.id

        service = ActivityService(context.db)
        activities = service.get_activities(user_id=user_id, limit=20)
        return {
            "count": len(activities),
            "activities": [
                {
                    "id": a.id,
                    "activity_type": a.activity_type,
                    "description": a.description,
                    "user": a.user.name if a.user else "System",
                    "created_at": str(a.created_at)
                }
                for a in activities
            ]
        }

# 12. GetUserEmailsTool
class GetUserEmailsArgs(BaseModel):
    urgency: Optional[str] = Field(None, description="Optional urgency filter (CRITICAL, HIGH, MEDIUM, LOW)")
    category: Optional[str] = Field(None, description="Optional category filter (CLIENT_BUG, MEETING_REQUEST, APPROVAL, GENERAL)")
    status: Optional[str] = Field(None, description="Optional status filter (UNREAD, ACTIONED)")

class GetUserEmailsTool(BaseTool):
    name = "get_user_emails"
    description = "Retrieve list of incoming emails for the user with AI urgency classification, categories, and draft replies."
    category = "EMAIL_TOOLS"
    risk_level = "LOW_RISK"
    args_schema = GetUserEmailsArgs

    def execute(self, args: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        from app.services.email_service import EmailService
        service = EmailService(context.db)
        emails = service.get_user_emails(context.user.id, urgency_filter=args.get("urgency"))

        if args.get("category"):
            emails = [e for e in emails if e.category.upper() == args["category"].upper()]
        if args.get("status"):
            emails = [e for e in emails if e.status.upper() == args["status"].upper()]

        return {
            "count": len(emails),
            "urgency_filter": args.get("urgency"),
            "emails": [
                {
                    "id": e.id,
                    "sender": e.sender,
                    "sender_email": e.sender_email,
                    "subject": e.subject,
                    "urgency": e.urgency,
                    "category": e.category,
                    "ai_summary": e.ai_summary,
                    "ai_draft_reply": e.ai_draft_reply,
                    "status": e.status,
                    "created_at": str(e.created_at)
                }
                for e in emails
            ]
        }

# 13. GetDailyActionPlanTool
class GetDailyActionPlanArgs(BaseModel):
    user_identifier: Optional[str] = Field(None, description="Optional user name or ID to filter plan for")

class GetDailyActionPlanTool(BaseTool):
    name = "get_daily_action_plan"
    description = "Analyze user emails, active tasks, blockers, and scheduled meetings to build a prioritized daily action plan (What do I need to do today / What is critical now)."
    category = "TASK_TOOLS"
    risk_level = "LOW_RISK"
    args_schema = GetDailyActionPlanArgs

    def execute(self, args: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        from app.services.email_service import EmailService
        from app.services.meeting_service import MeetingService

        target_user = context.user
        include_private_emails = True
        if args.get("user_identifier"):
            u, _, _ = EntityResolver.resolve_user(context.db, args["user_identifier"])
            if u:
                target_user = u
                if u.id != context.user.id and context.user.role != "ADMIN":
                    # Enforce strict personal privacy isolation
                    if getattr(u, "email_privacy_locked", True):
                        include_private_emails = False

        # 1. Fetch Emails (Isolated to owner or authorized request)
        email_service = EmailService(context.db)
        if include_private_emails:
            all_emails = email_service.get_user_emails(target_user.id)
            critical_emails = [e for e in all_emails if e.urgency == "CRITICAL" and e.status != "ACTIONED"]
            high_emails = [e for e in all_emails if e.urgency == "HIGH" and e.status != "ACTIONED"]
        else:
            critical_emails = []
            high_emails = []

        # 2. Fetch Assigned Tasks
        task_service = TaskService(context.db)
        user_tasks = task_service.get_all_tasks(assignee_id=target_user.id)
        active_tasks = [t for t in user_tasks if t.status != "COMPLETED"]
        urgent_tasks = [t for t in active_tasks if t.priority == "URGENT"]
        high_tasks = [t for t in active_tasks if t.priority == "HIGH"]
        in_progress_tasks = [t for t in active_tasks if t.status == "IN_PROGRESS" and t.priority not in ("URGENT", "HIGH")]

        # 3. Fetch Blockers
        blocker_service = BlockerService(context.db)
        all_blockers = blocker_service.get_all_blockers(status_filter="OPEN")
        user_blockers = [b for b in all_blockers if b.task and b.task.assignee_id == target_user.id]

        # 4. Fetch Meetings
        meeting_service = MeetingService(context.db)
        user_meetings = meeting_service.get_user_meetings(target_user.id)

        return {
            "user_name": target_user.name,
            "critical_emails": [
                {"subject": e.subject, "sender": e.sender, "ai_summary": e.ai_summary, "urgency": e.urgency}
                for e in critical_emails
            ],
            "high_emails": [
                {"subject": e.subject, "sender": e.sender, "ai_summary": e.ai_summary, "urgency": e.urgency}
                for e in high_emails
            ],
            "urgent_tasks": [
                {"title": t.title, "project": t.project.name if t.project else "N/A", "status": t.status, "priority": t.priority}
                for t in urgent_tasks
            ],
            "high_tasks": [
                {"title": t.title, "project": t.project.name if t.project else "N/A", "status": t.status, "priority": t.priority}
                for t in high_tasks
            ],
            "in_progress_tasks": [
                {"title": t.title, "project": t.project.name if t.project else "N/A", "status": t.status, "priority": t.priority}
                for t in in_progress_tasks
            ],
            "blockers": [
                {"task_title": b.task.title if b.task else "Task", "description": b.description, "severity": b.severity}
                for b in user_blockers
            ],
            "meetings": [
                {"title": m.title, "start_time": str(m.start_time), "meeting_link": m.meeting_link}
                for m in user_meetings
            ],
            "total_critical_items": len(critical_emails) + len(urgent_tasks) + len(user_blockers)
        }

# Register all read tools
def register_read_tools():
    registry.register(GetProjectsTool())
    registry.register(GetProjectTool())
    registry.register(GetTasksTool())
    registry.register(SearchTasksTool())
    registry.register(GetTaskTool())
    registry.register(GetUserTool())
    registry.register(GetTeamMembersTool())
    registry.register(GetTeamWorkloadTool())
    registry.register(GetUserTasksTool())
    registry.register(GetBlockersTool())
    registry.register(GetUserActivityTool())
    registry.register(GetUserEmailsTool())
    registry.register(GetDailyActionPlanTool())

