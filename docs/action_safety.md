# AI Action Safety & Authorization Protocol

## Mandatory Execution Protocol

When an AI Agent acts on behalf of a user in future phases, it MUST adhere to strict security pipeline rules:

```
1. User Authentication   ──► Validate JWT access token & user identity
2. Role Check            ──► Verify user permissions (ADMIN, MANAGER, MEMBER)
3. Schema Validation     ──► Enforce Pydantic validation on tool parameters
4. Confirmation Gate     ──► High-risk operations require explicit user approval
5. Service Execution     ──► Execute action through core Service layer
6. Audit Logging         ──► Record Activity entry with user_id & metadata
```

## Risk Classification Matrix

| Action Type | Operation | Risk Level | Confirmation Required? |
|---|---|---|---|
| READ | `get_projects`, `get_tasks`, `get_blockers` | LOW | No |
| WRITE | `create_task`, `add_comment`, `change_status` | MEDIUM | No |
| HIGH-RISK WRITE | `delete_task`, `delete_project`, `reassign_owner` | HIGH | **YES (User confirmation token)** |
| EXTERNAL ACTION | `send_client_email`, `send_whatsapp_msg` | HIGH | **YES (User confirmation token)** |
