import re
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from app.tools.registry import BaseTool, ToolContext, registry
from app.tools.entity_resolver import EntityResolver
from app.services.project_service import ProjectService
from app.services.task_service import TaskService
from app.services.blocker_service import BlockerService
from app.services.user_service import UserService
from app.schemas.project import ProjectCreate
from app.schemas.task import TaskCreate, TaskUpdate
from app.schemas.blocker import BlockerCreate, BlockerUpdate

# 0. CreateProjectTool
class CreateProjectArgs(BaseModel):
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")

class CreateProjectTool(BaseTool):
    name = "create_project"
    description = "Create a new project. (Requires ADMIN or MANAGER role)"
    category = "PROJECT_TOOLS"
    risk_level = "NORMAL_WRITE"
    args_schema = CreateProjectArgs

    def execute(self, args: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        service = ProjectService(context.db)
        project = service.create_project(
            ProjectCreate(name=args["name"], description=args.get("description"), owner_id=context.user.id),
            context.user
        )
        return {
            "success": True,
            "project_id": project.id,
            "name": project.name,
            "status": project.status
        }

# 1. CreateTaskTool
class CreateTaskArgs(BaseModel):
    title: str = Field(..., description="Title of the new task")
    project_identifier: Optional[str] = Field(None, description="Project name or UUID")
    description: Optional[str] = Field(None, description="Task details")
    assignee_identifier: Optional[str] = Field(None, description="Assignee user name, email, or UUID")
    priority: Optional[str] = Field("MEDIUM", description="Task priority (LOW, MEDIUM, HIGH, URGENT)")
    due_date_expression: Optional[str] = Field(None, description="Optional due date expression (e.g. 'today 6pm', 'tomorrow', 'Sept 15')")

class CreateTaskTool(BaseTool):
    name = "create_task"
    description = "Create a new project task, set priority, set due date, and optionally assign to a team member."
    category = "TASK_TOOLS"
    risk_level = "NORMAL_WRITE"
    args_schema = CreateTaskArgs

    def execute(self, args: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        proj_service = ProjectService(context.db)
        all_projects = proj_service.get_all_projects()
        project_names = [p.name for p in all_projects]

        project_query = args.get("project_identifier")
        project_id = None

        if not project_query:
            if all_projects:
                project_id = all_projects[-1].id
            else:
                return {
                    "error": "No active projects found in organization. Please create a project first.",
                    "needs_clarification": True
                }
        else:
            project, candidates, err = EntityResolver.resolve_project(context.db, project_query)
            if err or not project:
                cand_names = [p.name for p in candidates] if candidates else project_names
                proj_list_str = "\n".join([f"- {name}" for name in cand_names])
                return {
                    "error": f"Could not find project '{project_query}'. Which project did you mean?\n\nAvailable Projects:\n{proj_list_str}",
                    "needs_clarification": True,
                    "field": "project_identifier",
                    "available_projects": cand_names
                }
            project_id = project.id

        # Resolve assignee
        assignee_id = None
        if args.get("assignee_identifier"):
            user, candidates, err = EntityResolver.resolve_user(context.db, args["assignee_identifier"])
            if err or not user:
                user_service = UserService(context.db)
                all_users = user_service.get_all_users()
                user_names = [u.name for u in (candidates if candidates else all_users)]
                user_list_str = "\n".join([f"- {name}" for name in user_names])
                return {
                    "error": f"Could not find team member '{args['assignee_identifier']}'. Who would you like to assign this task to?\n\nAvailable Team Members:\n{user_list_str}",
                    "needs_clarification": True,
                    "field": "assignee_identifier",
                    "available_users": user_names
                }
            assignee_id = user.id

        due_date_dt = None
        if args.get("due_date_expression"):
            from app.services.meeting_service import MeetingService
            due_date_dt = MeetingService(context.db).parse_datetime_expression(args["due_date_expression"])

        service = TaskService(context.db)
        task_in = TaskCreate(
            project_id=project_id,
            title=args["title"],
            description=args.get("description"),
            priority=args.get("priority", "MEDIUM"),
            assignee_id=assignee_id,
            due_date=due_date_dt
        )
        task = service.create_task(task_in, context.user)

        return {
            "success": True,
            "task_id": task.id,
            "title": task.title,
            "status": task.status,
            "priority": task.priority,
            "due_date": str(task.due_date) if task.due_date else None,
            "project_name": task.project.name if task.project else None,
            "assignee": task.assignee.name if task.assignee else "Unassigned"
        }

# 2. AssignTaskTool (SUPPORT SCOPED PROJECT CONTEXT)
class AssignTaskArgs(BaseModel):
    task_identifier: str = Field(..., description="Task title or UUID")
    assignee_identifier: str = Field(..., description="Assignee user name, email, or UUID")
    project_identifier: Optional[str] = Field(None, description="Optional project name or UUID to scope task resolution")

class AssignTaskTool(BaseTool):
    name = "assign_task"
    description = "Reassign an existing task to another team member."
    category = "TASK_TOOLS"
    risk_level = "NORMAL_WRITE"
    args_schema = AssignTaskArgs

    def execute(self, args: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        project_id = None
        project_obj = None
        if args.get("project_identifier"):
            project_obj, _, _ = EntityResolver.resolve_project(context.db, args["project_identifier"])
            if project_obj:
                project_id = project_obj.id

        raw_title = args["task_identifier"].strip()
        clean_title = re.sub(r"^(?:task\s+)?(?:to\s+)?(?:work\s+on\s+the|work\s+on|do\s+the|do|build\s+the|build|implement\s+the|implement)\s+", "", raw_title, flags=re.IGNORECASE).strip()
        clean_title = re.sub(r"^the\s+", "", clean_title, flags=re.IGNORECASE).strip()
        clean_title = re.sub(r"^(?:task\s+)", "", clean_title, flags=re.IGNORECASE).strip()
        if not clean_title:
            clean_title = raw_title

        task, candidates, err = EntityResolver.resolve_task(context.db, clean_title, project_id=project_id)
        if not task and raw_title != clean_title:
            task, candidates, err = EntityResolver.resolve_task(context.db, raw_title, project_id=project_id)

        if err or not task:
            cand_titles = [t.title for t in candidates] if candidates else []
            if cand_titles:
                cand_str = "\n".join([f"- {t}" for t in cand_titles])
                return {
                    "error": f"Multiple tasks matched '{clean_title}'. Which task did you mean?\n\n{cand_str}",
                    "needs_clarification": True,
                    "field": "task_identifier",
                    "available_tasks": cand_titles
                }
            return {
                "error": f"Could not find task '{clean_title}'. Please specify a valid existing task title or UUID to reassign.",
                "needs_clarification": True,
                "field": "task_identifier"
            }

        user, candidates, err = EntityResolver.resolve_user(context.db, args["assignee_identifier"])
        if err or not user:
            return {"error": f"Could not resolve user '{args['assignee_identifier']}': {err}"}

        service = TaskService(context.db)
        updated_task = service.assign_task(task.id, user.id, context.user)

        return {
            "success": True,
            "task_id": updated_task.id,
            "task_title": updated_task.title,
            "new_assignee": user.name
        }

# 3. UpdateTaskTool
class UpdateTaskArgs(BaseModel):
    task_identifier: str = Field(..., description="Task title or UUID")
    priority: Optional[str] = Field(None, description="New priority (LOW, MEDIUM, HIGH, URGENT)")
    description: Optional[str] = Field(None, description="New description")

class UpdateTaskTool(BaseTool):
    name = "update_task"
    description = "Update task details such as priority or description."
    category = "TASK_TOOLS"
    risk_level = "NORMAL_WRITE"
    args_schema = UpdateTaskArgs

    def execute(self, args: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        task, _, err = EntityResolver.resolve_task(context.db, args["task_identifier"])
        if err or not task:
            return {"error": f"Could not resolve task '{args['task_identifier']}': {err}"}

        service = TaskService(context.db)
        updated = service.update_task(
            task.id,
            TaskUpdate(priority=args.get("priority"), description=args.get("description")),
            context.user
        )

        return {
            "success": True,
            "task_id": updated.id,
            "title": updated.title,
            "priority": updated.priority
        }

# 4. ChangeTaskStatusTool
class ChangeTaskStatusArgs(BaseModel):
    task_identifier: str = Field(..., description="Task title or UUID")
    status: str = Field(..., description="New task status (TODO, IN_PROGRESS, IN_REVIEW, COMPLETED, BLOCKED)")

class ChangeTaskStatusTool(BaseTool):
    name = "change_task_status"
    description = "Change task status (e.g. Move task to IN_PROGRESS or COMPLETED)."
    category = "TASK_TOOLS"
    risk_level = "NORMAL_WRITE"
    args_schema = ChangeTaskStatusArgs

    def execute(self, args: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        task, _, err = EntityResolver.resolve_task(context.db, args["task_identifier"])
        if err or not task:
            return {"error": f"Could not resolve task '{args['task_identifier']}': {err}"}

        service = TaskService(context.db)
        updated = service.update_task(
            task.id,
            TaskUpdate(status=args["status"]),
            context.user
        )

        return {
            "success": True,
            "task_id": updated.id,
            "title": updated.title,
            "new_status": updated.status
        }

# 5. CreateBlockerTool
class CreateBlockerArgs(BaseModel):
    task_identifier: str = Field(..., description="Task title or UUID")
    description: str = Field(..., description="Reason for blocker")
    severity: Optional[str] = Field("HIGH", description="Blocker severity (LOW, MEDIUM, HIGH, CRITICAL)")

class CreateBlockerTool(BaseTool):
    name = "create_blocker"
    description = "Report a blocker on a task. Automatically sets task status to BLOCKED."
    category = "BLOCKER_TOOLS"
    risk_level = "NORMAL_WRITE"
    args_schema = CreateBlockerArgs

    def execute(self, args: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        task, _, err = EntityResolver.resolve_task(context.db, args["task_identifier"])
        if err or not task:
            return {"error": f"Could not resolve task '{args['task_identifier']}': {err}"}

        service = BlockerService(context.db)
        blocker = service.create_blocker(
            BlockerCreate(task_id=task.id, description=args["description"], severity=args.get("severity", "HIGH")),
            context.user
        )

        return {
            "success": True,
            "blocker_id": blocker.id,
            "task_title": task.title,
            "task_status": "BLOCKED",
            "description": blocker.description
        }

# 6. ResolveBlockerTool
class ResolveBlockerArgs(BaseModel):
    task_identifier: Optional[str] = Field(None, description="Task title or UUID")
    blocker_id: Optional[str] = Field(None, description="Blocker UUID")

class ResolveBlockerTool(BaseTool):
    name = "resolve_blocker"
    description = "Resolve a task blocker and unblock task status."
    category = "BLOCKER_TOOLS"
    risk_level = "NORMAL_WRITE"
    args_schema = ResolveBlockerArgs

    def execute(self, args: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        service = BlockerService(context.db)
        target_blocker = None

        if args.get("blocker_id"):
            target_blocker = service.get_blocker_by_id(args["blocker_id"])
        elif args.get("task_identifier"):
            task, _, err = EntityResolver.resolve_task(context.db, args["task_identifier"])
            if task:
                open_blockers = [b for b in task.blockers if b.status == "OPEN"]
                if open_blockers:
                    target_blocker = open_blockers[0]

        if not target_blocker:
            return {"error": "Could not find an open blocker matching parameters."}

        resolved = service.update_blocker(
            target_blocker.id,
            BlockerUpdate(status="RESOLVED"),
            context.user
        )

        return {
            "success": True,
            "blocker_id": resolved.id,
            "status": resolved.status,
            "resolved_at": str(resolved.resolved_at)
        }

# 7. ScheduleMeetingTool
class ScheduleMeetingArgs(BaseModel):
    attendee_identifier: str = Field(..., description="Name, email, or user identifier of person to schedule meeting with (e.g., 'Selva')")
    title: Optional[str] = Field(None, description="Title/topic of the meeting")
    date_time: Optional[str] = Field("today 6pm", description="Scheduled date and time expression (e.g., 'today 6pm', 'tomorrow 10am')")
    duration_minutes: Optional[int] = Field(30, description="Duration of meeting in minutes")
    description: Optional[str] = Field(None, description="Optional agenda or meeting notes")

class ScheduleMeetingTool(BaseTool):
    name = "schedule_meeting"
    description = "Schedule a meeting/sync with team member(s), generate a Google Meet video link, and automatically notify all attendees."
    category = "TEAM_TOOLS"
    risk_level = "NORMAL_WRITE"
    args_schema = ScheduleMeetingArgs

    def execute(self, args: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        from app.services.meeting_service import MeetingService
        service = MeetingService(context.db)
        meeting, err = service.schedule_meeting(
            organizer=context.user,
            attendee_query=args["attendee_identifier"],
            title=args.get("title"),
            date_time_str=args.get("date_time", "today 6pm"),
            duration_minutes=args.get("duration_minutes", 30),
            description=args.get("description")
        )
        if err or not meeting:
            return {"error": f"Failed to schedule meeting: {err}"}

        local_start = meeting.start_time.astimezone() if meeting.start_time.tzinfo else meeting.start_time
        formatted_time = local_start.strftime('%b %d at %I:%M %p')

        return {
            "success": True,
            "meeting_id": meeting.id,
            "title": meeting.title,
            "start_time": meeting.start_time.isoformat(),
            "meeting_link": meeting.meeting_link,
            "attendees_notified": True,
            "message": f"Meeting '{meeting.title}' scheduled for {formatted_time}. Google Meet Link: {meeting.meeting_link}"
        }

# 11. SendEmailReplyTool
class SendEmailReplyArgs(BaseModel):
    email_id: str = Field(..., description="ID of the email to reply to")
    custom_reply: Optional[str] = Field(None, description="Optional custom reply content")

class SendEmailReplyTool(BaseTool):
    name = "send_email_reply"
    description = "Approve and send an AI-generated or custom reply to an incoming email in the Smart Email Inbox."
    category = "EMAIL_TOOLS"
    risk_level = "NORMAL_WRITE"
    args_schema = SendEmailReplyArgs

    def execute(self, args: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        from app.services.email_service import EmailService
        service = EmailService(context.db)
        item = service.send_ai_reply(args["email_id"], context.user.id, custom_reply=args.get("custom_reply"))
        return {
            "success": True,
            "email_id": item.id,
            "sender": item.sender,
            "sender_email": item.sender_email,
            "message": f"Successfully sent AI reply to {item.sender_email} for subject '{item.subject}'"
        }

# Register all write tools
def register_write_tools():
    registry.register(CreateProjectTool())
    registry.register(CreateTaskTool())
    registry.register(AssignTaskTool())
    registry.register(UpdateTaskTool())
    registry.register(ChangeTaskStatusTool())
    registry.register(CreateBlockerTool())
    registry.register(ResolveBlockerTool())
    registry.register(ScheduleMeetingTool())
    registry.register(SendEmailReplyTool())
