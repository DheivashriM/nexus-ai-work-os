import json
from typing import List, Dict, Any, Tuple
from app.agents.context import AgentContext
from app.tools.registry import registry, ToolContext
from app.agents.safety import SafetyChecker
from app.models.ai_models import AIActionLog
from app.schemas.ai_schemas import ToolExecutionStep

class AgentExecutor:
    def __init__(self, context: AgentContext):
        self.context = context

    def execute_tool_calls(
        self,
        tool_calls: List[Any]
    ) -> Tuple[List[ToolExecutionStep], List[str], List[Dict[str, Any]]]:
        """
        Executes a batch of tool call requests.
        Returns (execution_steps, action_summaries, tool_result_messages)
        """
        steps: List[ToolExecutionStep] = []
        action_summaries: List[str] = []
        tool_messages: List[Dict[str, Any]] = []

        for idx, call in enumerate(tool_calls, start=1):
            tool_name = call.tool_name
            args = call.arguments or {}

            tool = registry.get_tool(tool_name)
            if not tool:
                steps.append(ToolExecutionStep(
                    step_number=idx,
                    tool_name=tool_name,
                    description=f"Unknown tool '{tool_name}'",
                    status="FAILED",
                    arguments=args,
                    result={"error": f"Tool '{tool_name}' not registered."}
                ))
                continue

            # 1. Authorization check (Enforced using ACTOR = context.user)
            if not SafetyChecker.is_authorized(tool_name, args, self.context.user):
                steps.append(ToolExecutionStep(
                    step_number=idx,
                    tool_name=tool_name,
                    description=f"Unauthorized access for tool '{tool_name}'",
                    status="UNAUTHORIZED",
                    arguments=args,
                    result={"error": "Permission denied."}
                ))
                self._log_action(tool_name, args, {"error": "Permission denied"}, "UNAUTHORIZED")
                action_summaries.append(f"Permission denied for operation '{tool_name}'.")
                continue

            # 2. Tool Execution
            tool_ctx = ToolContext(user=self.context.user, db=self.context.db, conversation_id=self.context.conversation_id)
            try:
                result = tool.execute(args, tool_ctx)
                is_success = "error" not in result

                # 3. Post-execution Verification
                verified = self._verify_action(tool_name, result)
                status_str = "SUCCESS" if (is_success and verified) else "FAILED"

                steps.append(ToolExecutionStep(
                    step_number=idx,
                    tool_name=tool_name,
                    description=f"Executed tool '{tool_name}'",
                    status=status_str,
                    arguments=args,
                    result=result
                ))

                # 4. Data-Driven Summary Construction
                summary = self._build_summary(tool_name, args, result)
                action_summaries.append(summary)

                # 5. Audit Logging
                self._log_action(tool_name, args, result, status_str)

                tool_messages.append({
                    "role": "tool",
                    "content": json.dumps(result),
                    "tool_call_id": call.id
                })

            except Exception as e:
                err_dict = {"error": f"Execution error in {tool_name}: {str(e)}"}
                steps.append(ToolExecutionStep(
                    step_number=idx,
                    tool_name=tool_name,
                    description=f"Error executing '{tool_name}'",
                    status="FAILED",
                    arguments=args,
                    result=err_dict
                ))
                self._log_action(tool_name, args, err_dict, "FAILED")
                action_summaries.append(f"Failed execution of '{tool_name}': {str(e)}")

        return steps, action_summaries, tool_messages

    def _verify_action(self, tool_name: str, result: Dict[str, Any]) -> bool:
        if "error" in result:
            return False
        if tool_name == "change_task_status":
            return result.get("new_status") is not None
        if tool_name == "assign_task":
            return result.get("new_assignee") is not None
        if tool_name == "create_task":
            return result.get("task_id") is not None
        if tool_name == "create_blocker":
            return result.get("task_status") == "BLOCKED"
        return True

    def _build_summary(self, tool_name: str, args: Dict[str, Any], result: Dict[str, Any]) -> str:
        if "error" in result:
            return f"Error: {result['error']}"

        if tool_name == "get_team_members":
            users = result.get("users", [])
            if not users:
                return "No team members found."
            items = [f"- **{u['name']}** — `{u['role']}` | ⚡ {u['active_tasks_count']} active tasks" for u in users]
            return "### 👥 Team Roster & Active Workloads\n\n" + "\n".join(items)

        if tool_name == "get_team_workload":
            workloads = result.get("workloads", [])
            most_loaded = result.get("most_loaded_member", "None")
            items = [f"- **{w['name']}**: {w['active_tasks_count']} active tasks" for w in workloads]
            return f"### 📊 Team Workload Summary\n\n" + "\n".join(items) + f"\n\n🔥 **Highest Workload:** {most_loaded}"

        if tool_name == "search_tasks":
            tasks = result.get("tasks", [])
            if tasks:
                t = tasks[0]
                return f"### 🔍 Found Matching Task\n\n- **Title:** {t['title']}\n- **Project:** {t.get('project') or 'N/A'}\n- **Assignee:** {t['assignee']}\n- **Status:** `{t['status']}`"
            candidates = result.get("candidates", [])
            if candidates:
                cand_items = [f"- **{c['title']}** (Project: {c.get('project') or 'N/A'}, Assignee: {c['assignee']})" for c in candidates]
                return f"### 🔍 Multiple Tasks Found\n\n" + "\n".join(cand_items)
            return "No matching tasks found."

        if tool_name == "get_user_tasks":
            user_name = result.get("user", "User")
            tasks = result.get("tasks", [])
            active_tasks = [t for t in tasks if t.get("status") != "COMPLETED"]
            if not active_tasks:
                return f"### 📋 Tasks for {user_name}\n\n{user_name} currently has 0 active tasks assigned."
            
            task_items = [
                f"- **{t['title']}**\n  - **Status:** `{t['status']}` | **Priority:** `{t['priority']}`\n  - **Project:** {t.get('project') or 'N/A'}"
                for t in active_tasks
            ]
            return f"### 📋 Active Tasks for {user_name} ({len(active_tasks)} Tasks)\n\n" + "\n".join(task_items)

        if tool_name == "get_projects":
            projects = result.get("projects", [])
            if not projects:
                return "No projects found in the organization."
            proj_items = [f"- 🟢 **{p['name']}** — `{p['status']}` (Priority: `{p['priority']}`, Owner: {p['owner']})" for p in projects]
            return f"### 📁 Organization Projects ({len(projects)} Total)\n\n" + "\n".join(proj_items)

        if tool_name == "get_tasks":
            tasks = result.get("tasks", [])
            if not tasks:
                return "No tasks found matching criteria."
            task_items = [f"- **{t['title']}** (Assignee: {t['assignee']}, Status: `{t['status']}`, Priority: `{t['priority']}`)" for t in tasks[:10]]
            return f"### 📋 Tasks List ({len(tasks)} Total)\n\n" + "\n".join(task_items)

        if tool_name == "get_task":
            title = result.get("title", "Task")
            status = result.get("status", "N/A")
            priority = result.get("priority", "N/A")
            assignee = result.get("assignee", "Unassigned")
            desc = result.get("description", "No description provided.")
            comments = result.get("comments", [])
            blockers = result.get("blockers", [])

            lines = [
                f"### 📌 Task Details: {title}",
                f"- **Status:** `{status}` | **Priority:** `{priority}`",
                f"- **Assignee:** {assignee}",
                f"- **Description:** {desc}"
            ]
            if comments:
                latest = comments[-1]
                lines.append(f"- **Latest Comment:** *\"{latest['content']}\"* (by {latest['user']})")
            if blockers:
                open_b = [b for b in blockers if b.get("status") == "OPEN"]
                if open_b:
                    lines.append(f"- 🚨 **Active Blocker:** *\"{open_b[0]['description']}\"* (Severity: `{open_b[0]['severity']}`)")

            return "\n".join(lines)

        if tool_name == "get_blockers":
            blockers = result.get("blockers", [])
            if not blockers:
                return "No active blockers found."
            items = [f"- 🚨 **{b['description']}** on task *'{b['task_title']}'* (Severity: `{b['severity']}`)" for b in blockers]
            return f"### 🚨 Active Blockers ({len(blockers)} Total)\n\n" + "\n".join(items)

        if tool_name == "create_task":
            due_str = f"\n- **Due Date:** `{result.get('due_date')}`" if result.get("due_date") else ""
            return (
                f"### ✅ Task Created Successfully!\n\n"
                f"- **Title:** {result.get('title')}\n"
                f"- **Project:** {result.get('project_name') or 'N/A'}\n"
                f"- **Assignee:** {result.get('assignee')}\n"
                f"- **Status:** `{result.get('status')}` | **Priority:** `{result.get('priority')}`"
                f"{due_str}"
            )

        if tool_name == "assign_task":
            if result.get("created_new"):
                return (
                    f"### ✅ Task Created & Assigned!\n\n"
                    f"- **Task:** {result.get('task_title')}\n"
                    f"- **Project:** {result.get('project_name') or 'N/A'}\n"
                    f"- **Assignee:** {result.get('new_assignee')}"
                )
            return (
                f"### 👤 Task Reassigned!\n\n"
                f"- **Task:** {result.get('task_title')}\n"
                f"- **New Assignee:** {result.get('new_assignee')}"
            )

        if tool_name == "change_task_status":
            return (
                f"### 🔄 Task Status Updated!\n\n"
                f"- **Task:** {result.get('title')}\n"
                f"- **New Status:** `{result.get('new_status')}`"
            )

        if tool_name == "update_task":
            return (
                f"### ✏️ Task Details Updated!\n\n"
                f"- **Task:** {result.get('title')}\n"
                f"- **Priority:** `{result.get('priority')}`"
            )

        if tool_name == "create_blocker":
            return (
                f"### 🚨 Blocker Reported!\n\n"
                f"- **Task:** {result.get('task_title')}\n"
                f"- **Reason:** {result.get('description')}\n"
                f"- **Task Status:** `BLOCKED`"
            )

        if tool_name == "resolve_blocker":
            return f"### ✅ Blocker Resolved!\n\nTask status has been updated to `IN_PROGRESS`."

        if tool_name == "schedule_meeting":
            return (
                f"### 📅 Meeting Scheduled Successfully!\n\n"
                f"- **Title:** {result.get('title')}\n"
                f"- **Time:** {result.get('start_time')}\n"
                f"- **Google Meet Join Link:** {result.get('meeting_link')}\n"
                f"- **Attendees Notified:** ✅ Yes"
            )

        if tool_name == "get_user_emails":
            emails = result.get("emails", [])
            urg_filter = result.get("urgency_filter")
            if not emails:
                filter_str = f" with urgency `{urg_filter}`" if urg_filter else ""
                return f"### 📬 Smart Email Inbox\n\nNo emails found{filter_str}."

            badge_map = {"CRITICAL": "🔴 [CRITICAL]", "HIGH": "🟠 [HIGH]", "MEDIUM": "🟡 [MEDIUM]", "LOW": "🟢 [LOW]"}
            email_items = []
            for e in emails:
                badge = badge_map.get(e["urgency"], f"`{e['urgency']}`")
                status_str = f"`{e['status']}`"
                email_items.append(
                    f"- {badge} **{e['subject']}** — From **{e['sender']}** ({e['sender_email']})\n"
                    f"  - **AI Summary:** {e['ai_summary']}\n"
                    f"  - **Category:** `{e['category']}` | **Status:** {status_str}"
                )
            header = f"### 📬 Smart Email Inbox ({len(emails)} Emails" + (f" - Filter: {urg_filter}" if urg_filter else "") + ")\n\n"
            return header + "\n".join(email_items)

        if tool_name == "get_daily_action_plan":
            user_name = result.get("user_name", "You")
            crit_emails = result.get("critical_emails", [])
            high_emails = result.get("high_emails", [])
            urg_tasks = result.get("urgent_tasks", [])
            high_tasks = result.get("high_tasks", [])
            in_prog = result.get("in_progress_tasks", [])
            blockers = result.get("blockers", [])
            meetings = result.get("meetings", [])
            tot_crit = result.get("total_critical_items", 0)

            lines = [f"### 🎯 Daily Action Plan & Priorities for {user_name}\n"]

            lines.append("#### 🔴 CRITICAL / IMMEDIATE ACTION REQUIRED (Tackle First Now)")
            if not crit_emails and not urg_tasks and not blockers:
                lines.append("- *No emergency items or active blockers currently.*")
            else:
                for e in crit_emails:
                    lines.append(f"- ✉️ **[CRITICAL EMAIL] {e['subject']}** — From {e['sender']}\n  - *AI Summary:* {e['ai_summary']}")
                for t in urg_tasks:
                    lines.append(f"- ⚡ **[URGENT TASK] {t['title']}** (Project: `{t['project']}`, Status: `{t['status']}`)")
                for b in blockers:
                    lines.append(f"- 🚨 **[ACTIVE BLOCKER] {b['task_title']}**: *{b['description']}* (Severity: `{b['severity']}`)")

            lines.append("\n#### 🟠 HIGH PRIORITY ITEMS")
            if not high_emails and not high_tasks and not in_prog:
                lines.append("- *No additional high priority tasks or emails.*")
            else:
                for e in high_emails:
                    lines.append(f"- ✉️ **{e['subject']}** — From {e['sender']} ({e['ai_summary']})")
                for t in high_tasks:
                    lines.append(f"- 📋 **{t['title']}** (Project: `{t['project']}`, Status: `{t['status']}`)")
                for t in in_prog:
                    lines.append(f"- ⚙️ **{t['title']}** (In Progress)")

            lines.append("\n#### 📅 TODAY'S MEETINGS & SCHEDULE")
            if not meetings:
                lines.append("- *No meetings scheduled for today.*")
            else:
                for m in meetings:
                    lines.append(f"- 📹 **{m['title']}** at `{m['start_time']}` | [Join Google Meet]({m['meeting_link']})")

            lines.append("\n#### 💡 AI RECOMMENDED NEXT STEPS")
            if tot_crit > 0:
                lines.append(f"1. **Address the {tot_crit} critical item(s) listed above immediately** to prevent project delays.")
                lines.append("2. Review high priority tasks and send AI draft replies to urgent emails.")
            else:
                lines.append("1. All critical channels are clear! Focus on in-progress tasks and high priority deliverables.")

            return "\n".join(lines)

        return f"Executed {tool_name} successfully."

    def _log_action(self, tool_name: str, args: Dict[str, Any], result: Dict[str, Any], status: str):
        risk = SafetyChecker.classify_risk(tool_name)
        log = AIActionLog(
            conversation_id=self.context.conversation_id,
            user_id=self.context.user.id,
            tool_name=tool_name,
            target_resource=args.get("task_identifier") or args.get("project_identifier") or args.get("title"),
            risk_level=risk,
            arguments_json=args,
            result_json=result,
            status=status
        )
        self.context.db.add(log)
        self.context.db.commit()
