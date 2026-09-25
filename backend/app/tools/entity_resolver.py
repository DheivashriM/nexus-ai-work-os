"""
Entity Resolver Module
Provides deterministic entity resolution across database models (Users, Projects, Tasks)
by ID, name, email, or token matching. Ensures clean error handling without hardcoded guesses or silent side-effects.
"""
import re
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.task import Task
from app.models.project import Project

class EntityResolver:
    @staticmethod
    def resolve_user(db: Session, query: str) -> Tuple[Optional[User], Optional[List[User]], Optional[str]]:
        """
        Resolves a user by ID, exact name, partial name, or email.
        Returns (resolved_user, candidates_if_ambiguous, error_message)
        """
        if not query or not query.strip():
            return None, None, "User query is empty."
        
        query = query.strip()

        # 1. Try by exact ID
        user = db.query(User).filter(User.id == query).first()
        if user:
            return user, None, None

        # 2. Try by exact email
        user = db.query(User).filter(User.email.ilike(query)).first()
        if user:
            return user, None, None

        # 3. Try exact name match
        users = db.query(User).filter(User.name.ilike(query)).all()
        if len(users) == 1:
            return users[0], None, None
        elif len(users) > 1:
            unique_names = list(set(u.name for u in users))
            if len(unique_names) == 1:
                return users[0], None, None
            return None, users, f"Multiple users matched exact name '{query}': {', '.join(u.name for u in users)}."

        # 4. Try partial name match (first name / substring)
        users = db.query(User).filter(User.name.ilike(f"%{query}%")).all()
        if len(users) == 1:
            return users[0], None, None
        elif len(users) > 1:
            unique_names = list(set(u.name for u in users))
            if len(unique_names) == 1:
                return users[0], None, None
            names = list(set(u.name for u in users))
            return None, users, f"Multiple users found matching '{query}': {', '.join(names)}. Which one do you mean?"

        # 5. Try email prefix or space-normalized match (e.g. "user1" -> "user1@example.com" or "User 1")
        clean_query = query.replace(" ", "").lower()
        all_users = db.query(User).all()
        matched = [
            u for u in all_users
            if u.email.split("@")[0].replace(" ", "").lower() == clean_query
            or u.name.replace(" ", "").lower() == clean_query
            or clean_query in u.email.split("@")[0].replace(" ", "").lower()
            or clean_query in u.name.replace(" ", "").lower()
        ]
        if len(matched) == 1:
            return matched[0], None, None
        elif len(matched) > 1:
            names = list(set(u.name for u in matched))
            return None, matched, f"Multiple users found matching '{query}': {', '.join(names)}. Which one do you mean?"

        return None, None, f"Could not resolve team member '{query}': No user found matching '{query}'."

    @staticmethod
    def resolve_project(db: Session, query: str) -> Tuple[Optional[Project], Optional[List[Project]], Optional[str]]:
        """
        Resolves a project by ID or name (exact, partial, normalized).
        """
        if not query or not query.strip():
            return None, None, "Project query is empty."

        query = query.strip()

        # 1. Exact ID
        project = db.query(Project).filter(Project.id == query).first()
        if project:
            return project, None, None

        # 2. Exact Name
        projects = db.query(Project).filter(Project.name.ilike(query)).all()
        if len(projects) == 1:
            return projects[0], None, None
        elif len(projects) > 1:
            unique_names = list(set(p.name for p in projects))
            if len(unique_names) == 1:
                return projects[0], None, None

        # 3. Substring / Partial Name
        projects = db.query(Project).filter(Project.name.ilike(f"%{query}%")).all()
        if len(projects) == 1:
            return projects[0], None, None
        elif len(projects) > 1:
            unique_names = list(set(p.name for p in projects))
            if len(unique_names) == 1:
                return projects[0], None, None
            return None, projects, f"Multiple projects found matching '{query}': {', '.join(unique_names)}."

        # 4. Normalized Token Match with Stop Word Removal (e.g. "website on food project" -> "Website for food")
        stop_words = {"project", "projects", "task", "tasks", "the", "a", "an", "for", "on", "in", "under", "with", "to", "of", "app", "website", "site"}
        all_tokens = [t.lower() for t in re.split(r"\W+", query) if len(t) > 1]
        sig_tokens = [t for t in all_tokens if t not in stop_words and len(t) > 2]
        
        # Try with significant tokens first
        target_tokens = sig_tokens if sig_tokens else [t for t in all_tokens if len(t) > 2]
        if target_tokens:
            all_projs = db.query(Project).all()
            matched = [p for p in all_projs if all(t in p.name.lower() for t in target_tokens)]
            if len(matched) == 1:
                return matched[0], None, None
            elif len(matched) > 1:
                unique_names = list(set(p.name for p in matched))
                if len(unique_names) == 1:
                    return matched[0], None, None
                return None, matched, f"Multiple projects found matching '{query}'."

        return None, None, f"Could not resolve project '{query}': No project found matching '{query}'."

    @staticmethod
    def resolve_task(
        db: Session,
        query: str,
        project_id: Optional[str] = None
    ) -> Tuple[Optional[Task], Optional[List[Task]], Optional[str]]:
        """
        Resolves a task by ID or title substring, scoped by optional project_id filter.
        """
        if not query or not query.strip():
            return None, None, "Task query is empty."

        query = query.strip()

        # 1. Try by exact ID
        task = db.query(Task).filter(Task.id == query).first()
        if task:
            return task, None, None

        # Base query with project filter
        db_query = db.query(Task)
        if project_id:
            db_query = db_query.filter(Task.project_id == project_id)

        # 2. Exact title match
        exact_tasks = db_query.filter(Task.title.ilike(query)).all()
        if len(exact_tasks) == 1:
            return exact_tasks[0], None, None
        elif len(exact_tasks) > 1:
            unique_titles = list(set(t.title for t in exact_tasks))
            if len(unique_titles) == 1:
                return exact_tasks[0], None, None

        # 3. Partial title match
        partial_tasks = db_query.filter(Task.title.ilike(f"%{query}%")).all()
        if len(partial_tasks) == 1:
            return partial_tasks[0], None, None
        elif len(partial_tasks) > 1:
            unique_titles = list(set(t.title for t in partial_tasks))
            if len(unique_titles) == 1:
                return partial_tasks[0], None, None
            titles = [f"'{t.title}' (ID: {t.id[:8]})" for t in partial_tasks]
            return None, partial_tasks, f"I found multiple tasks matching '{query}': {', '.join(titles)}. Which one did you mean?"

        # 4. Token substring match (e.g. "api workflow" -> "API Workflow Configuration")
        tokens = [t for t in re.split(r"\W+", query) if len(t) > 2]
        if tokens:
            all_candidate_tasks = db_query.all()
            token_matched = [t for t in all_candidate_tasks if all(tok.lower() in t.title.lower() for tok in tokens)]
            if len(token_matched) == 1:
                return token_matched[0], None, None
            elif len(token_matched) > 1:
                unique_titles = list(set(t.title for t in token_matched))
                if len(unique_titles) == 1:
                    return token_matched[0], None, None
                titles = [f"'{t.title}'" for t in token_matched]
                return None, token_matched, f"I found multiple tasks matching '{query}': {', '.join(titles)}. Which one did you mean?"

        return None, None, f"Could not resolve task '{query}': No task found matching '{query}'."
