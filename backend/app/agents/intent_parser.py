"""
Intent Parser Module
Provides regex-based intent classification and entity slot parsing for rule-based mode.
Extracts structured intent parameters without relying on hardcoded user lists or dummy fallbacks.
"""
import re
from typing import List, Dict, Any, Optional
from app.agents.intent import StructuredIntent, EntitySlot

class IntentParser:
    @staticmethod
    def parse_user_prompt(
        messages: List[Dict[str, Any]],
        actor_id: str
    ) -> StructuredIntent:
        user_messages = [m for m in messages if m.get("role") == "user"]
        latest_text = user_messages[-1].get("content", "").strip() if user_messages else ""
        clean_text = re.sub(r"[\.\?\!]+$", "", latest_text).strip()
        lower = clean_text.lower()
        intent = StructuredIntent(intent_type="unknown", actor_id=actor_id)



        if "meeting" in lower or "schedule" in lower or "meet" in lower:
            intent.intent_type = "schedule_meeting"
            m_att = re.search(r"(?:meeting|meet|schedule)\s+(?:with|for)\s+([A-Za-z0-9\s]+?)(?:\s+(?:at|on|for|by|today|tonight|tomorrow|\d{1,2})|$)", clean_text, re.IGNORECASE)
            att_name = m_att.group(1).strip() if m_att else None
            
            m_time = re.search(r"(\d{1,2}(?::\d{2})?\s*(?:am|pm)?\s*(?:today|tonight|tomorrow)?|\btonight\b|\btoday\b|\btomorrow\b)", clean_text, re.IGNORECASE)
            time_str = m_time.group(1).strip() if m_time else "today"
            
            intent.task = EntitySlot(raw_text=f"Meeting with {att_name}" if att_name else "Project Meeting")
            if att_name:
                intent.assignee = EntitySlot(raw_text=att_name)
            intent.due_date = time_str
            return intent

        # Daily Plan / Action Plan Triggers
        daily_plan_phrases = [
            "need to do today", "do today", "should i do today", "my daily plan",
            "what is critical and what he need to do now", "what is critical and what i need to do",
            "what is critical", "my priorities", "what should i focus on", "what to do now", "today's priorities",
            "what i need to do", "what do i need to do", "things i must complete", "things to complete",
            "my schedule", "my agenda", "what do i have today", "what is assigned to me today",
            "tasks for me today", "my tasks today", "what should i complete today"
        ]
        if any(phrase in lower for phrase in daily_plan_phrases):
            intent.intent_type = "get_daily_action_plan"
            return intent

        # Email / Inbox Triggers
        email_phrases = ["mail", "mails", "email", "emails", "inbox"]
        if any(phrase in lower for phrase in email_phrases):
            intent.intent_type = "get_user_emails"
            if "critical" in lower:
                intent.priority = "CRITICAL"
            elif "urgent" in lower or "high" in lower:
                intent.priority = "HIGH"
            elif "medium" in lower:
                intent.priority = "MEDIUM"
            elif "low" in lower:
                intent.priority = "LOW"
            return intent
        # Create Task Triggers
        if "create" in lower or "add task" in lower or "make a task" in lower or "new task" in lower:
            intent.intent_type = "create_task"
            m_t = (
                re.search(r"(?:titled|called|named)\s+[*'\"`]*([^'*\"`\.\n]+)[*'\"`]*", clean_text, re.IGNORECASE) or
                re.search(r"task\s+(?:called|titled|named)?\s*[*'\"`]*([^'*\"`\.\n]+)[*'\"`]*", clean_text, re.IGNORECASE)
            )
            if m_t:
                raw_t = m_t.group(1).strip().strip("'\"`")
                raw_t = re.sub(r"^(?:called|titled|named|a|an|the)\s+", "", raw_t, flags=re.IGNORECASE).strip()
                intent.task = EntitySlot(raw_text=raw_t)
            else:
                raw_t = re.sub(r"^(?:create|make|add)\s+(?:a|an|the)?\s*(?:high-priority|low-priority|urgent|medium-priority)?\s*(?:task)?\s*", "", clean_text, flags=re.IGNORECASE).strip()
                intent.task = EntitySlot(raw_text=raw_t)

            m_u = re.search(r"(?:for|assigned to|assign to)\s+([A-Za-z0-9_\s]+?)(?:\s+in|\s+under|\s+for project|$)", clean_text, re.IGNORECASE)
            if m_u:
                intent.assignee = EntitySlot(raw_text=m_u.group(1).strip())

            m_p = re.search(r"(?:for project|under project|in project|under)\s+(?:the\s+)?([A-Za-z0-9_\s]+)", clean_text, re.IGNORECASE)
            if m_p:
                intent.project = EntitySlot(raw_text=m_p.group(1).strip())

            return intent

        if ("assign" in lower or "put" in lower or "give" in lower or "reassign" in lower or "have" in lower) and "create" not in lower:
            # 1. Pattern: assign [USER] to work on/do/build/implement [WORK] [for/in/under PROJECT]
            m_user_work = re.search(r"(?:assign|put|have|reassign)\s+([A-Za-z0-9_\s]+?)\s+(?:to\s+work\s+on|to\s+do|to\s+build|to\s+implement|to\s+handle|to\s+manage)\s+(.+)", clean_text, re.IGNORECASE)
            if m_user_work:
                raw_user = m_user_work.group(1).strip()
                raw_work = m_user_work.group(2).strip()

                p_match = re.search(r"\s+(?:for|in|under|on project|for project|under project)\s+(?:the\s+)?(.+)", raw_work, re.IGNORECASE)
                raw_project = None
                if p_match:
                    raw_project = p_match.group(1).strip()
                    raw_work = raw_work[:p_match.start()].strip()
                    raw_project = re.sub(r"\s+(?:project|projects|task|tasks)$", "", raw_project, flags=re.IGNORECASE).strip()

                clean_title = re.sub(r"^(?:work\s+on\s+the|work\s+on|do\s+the|do|build\s+the|build|implement\s+the|implement|the|a|an)\s+", "", raw_work, flags=re.IGNORECASE).strip()
                clean_title = re.sub(r"^the\s+", "", clean_title, flags=re.IGNORECASE).strip()

                intent.intent_type = "assign_task"
                intent.assignee = EntitySlot(raw_text=raw_user)
                intent.task = EntitySlot(raw_text=clean_title if clean_title else raw_work)
                if raw_project:
                    intent.project = EntitySlot(raw_text=raw_project)
                return intent

            # 2. Pattern: assign [WORK/PRONOUN] to [USER] (e.g. "Assign it to Sibi" or "Assign task A to User B")
            m_work_to_user = re.search(r"(?:assign|put|have|reassign|give)\s+(.+?)\s+to\s+([A-Za-z0-9_\s]+)$", clean_text, re.IGNORECASE)
            if m_work_to_user:
                raw_work = m_work_to_user.group(1).strip()
                raw_user = m_work_to_user.group(2).strip()

                p_match = re.search(r"\s+(?:for|in|under|on project|for project|under project)\s+(?:the\s+)?(.+)", raw_work, re.IGNORECASE)
                raw_project = None
                if p_match:
                    raw_project = p_match.group(1).strip()
                    raw_work = raw_work[:p_match.start()].strip()
                    raw_project = re.sub(r"\s+(?:project|projects|task|tasks)$", "", raw_project, flags=re.IGNORECASE).strip()

                clean_title = re.sub(r"^(?:work\s+on\s+the|work\s+on|do\s+the|do|build\s+the|build|implement\s+the|implement|the|a|an)\s+", "", raw_work, flags=re.IGNORECASE).strip()
                clean_title = re.sub(r"^the\s+", "", clean_title, flags=re.IGNORECASE).strip()

                intent.intent_type = "assign_task"
                intent.assignee = EntitySlot(raw_text=raw_user)
                intent.task = EntitySlot(raw_text=clean_title if clean_title else raw_work)
                if raw_project:
                    intent.project = EntitySlot(raw_text=raw_project)
                return intent

            # 3. Pattern: assign to work on/do/build [WORK] [for/in/under PROJECT] (No explicit user name)
            m_no_user = re.search(r"(?:assign|reassign)\s+(?:to\s+work\s+on|work\s+on|to\s+do|to\s+build|to)\s+(.+)", clean_text, re.IGNORECASE)
            if m_no_user:
                raw_work = m_no_user.group(1).strip()
                p_match = re.search(r"\s+(?:for|in|under|on project|for project)\s+(?:the\s+)?(.+)", raw_work, re.IGNORECASE)
                raw_project = None
                if p_match:
                    raw_project = p_match.group(1).strip()
                    raw_work = raw_work[:p_match.start()].strip()
                    raw_project = re.sub(r"\s+(?:project|projects|task|tasks)$", "", raw_project, flags=re.IGNORECASE).strip()

                clean_title = re.sub(r"^(?:work\s+on\s+the|work\s+on|do\s+the|do|build\s+the|build|implement\s+the|implement|the|a|an)\s+", "", raw_work, flags=re.IGNORECASE).strip()
                intent.intent_type = "assign_task"
                intent.task = EntitySlot(raw_text=clean_title if clean_title else raw_work)
                if raw_project:
                    intent.project = EntitySlot(raw_text=raw_project)
                return intent
        # Only parse query intents if not an action prompt
        if not ("assign" in lower or "create" in lower or "put" in lower or "give" in lower or "reassign" in lower):
            if "workload" in lower or "overloaded" in lower or "most active" in lower or "most tasks" in lower:
                intent.intent_type = "get_team_workload"
                return intent
            if "team members" in lower or "team roster" in lower or "who works" in lower or "who is in the team" in lower:
                intent.intent_type = "get_team_members"
                return intent

            user_task_triggers = ["doing", "working", "task", "tasks", "assigned", "handling", "under", "for", "of", "belonging"]
            if any(trig in lower for trig in user_task_triggers):
                cand = None
                m_prep = re.search(r"\b(?:under|for|of|assigned to|with|belonging to|handled by|managed by)\s+(\w+)", clean_text, re.IGNORECASE)
                if m_prep:
                    cand = m_prep.group(1).strip()
                if not cand:
                    m_poss = re.search(r"\b(\w+)'s\s+(?:tasks?|work|job|assignments?)\b", clean_text, re.IGNORECASE)
                    if m_poss:
                        cand = m_poss.group(1).strip()
                if not cand:
                    m_do = re.search(r"\b(?:is|does|has)\s+(\w+)\s+(?:doing|working|handling|managing|have|assigned)\b", clean_text, re.IGNORECASE)
                    if m_do:
                        cand = m_do.group(1).strip()
                if cand:
                    intent.intent_type = "get_user_tasks"
                    intent.user_query = EntitySlot(raw_text=cand)
                    return intent
                if cand:
                    intent.intent_type = "get_user_tasks"
                    intent.assignee = EntitySlot(raw_text=cand)
                    return intent
        return intent