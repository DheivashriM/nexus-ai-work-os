# AI Tools Specification (Phase 2 Roadmap)

This document specifies the function-calling interfaces for future AI Agents to interact with the backend service layer.

## Standard Tool Definitions

### 1. `get_projects`
- **Description**: Fetch active projects with progress metrics and assigned team members.
- **Parameters**: `status` (optional enum), `limit` (int)
- **Backend Service Invoked**: `ProjectService.get_projects()`

### 2. `get_tasks`
- **Description**: Search tasks by project, assignee, status, or priority.
- **Parameters**: `project_id` (UUID), `assignee_id` (UUID), `status` (enum), `priority` (enum)
- **Backend Service Invoked**: `TaskService.get_tasks()`

### 3. `create_task`
- **Description**: Create a new task in a project and assign to a team member.
- **Parameters**: `project_id` (UUID), `title` (str), `description` (str), `assignee_id` (UUID), `due_date` (datetime), `priority` (enum)
- **Backend Service Invoked**: `TaskService.create_task()`
- **Permission Required**: `can_create_task`

### 4. `assign_task`
- **Description**: Reassign an existing task to another user.
- **Parameters**: `task_id` (UUID), `assignee_id` (UUID)
- **Backend Service Invoked**: `TaskService.assign_task()`

### 5. `change_task_status`
- **Description**: Update status of a task (e.g. `TODO` -> `IN_PROGRESS` or `BLOCKED`).
- **Parameters**: `task_id` (UUID), `status` (enum)
- **Backend Service Invoked**: `TaskService.update_task_status()`

### 6. `get_blockers`
- **Description**: Retrieve active blockers blocking project progress.
- **Parameters**: `project_id` (optional UUID), `status` (enum: OPEN/RESOLVED)
- **Backend Service Invoked**: `BlockerService.get_blockers()`

### 7. `get_user_activity`
- **Description**: Get audit logs of actions performed by or regarding a user/project.
- **Parameters**: `user_id` (UUID), `project_id` (UUID), `limit` (int)
- **Backend Service Invoked**: `ActivityService.get_activities()`

## Tool Execution Flow
```
User Natural Language Prompt
            │
            ▼
   LLM Function Call Selection
            │
            ▼
   JWT / Auth Context Propagation
            │
            ▼
   Backend Permission Validation (`PermissionService`)
            │
            ▼
   Service Layer Execution & Activity Audit Log Entry
```
