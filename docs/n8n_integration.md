# n8n Automation & Integration Architecture

## Architectural Role of n8n
In future phases, n8n serves as the primary external integration and workflow automation orchestration engine.

```
External Systems (Gmail, Slack, Zoom, Google Calendar)
                           │
                           ▼  Webhooks / API Triggers
                      n8n Workflows
                           │
                           ▼  Authenticated Backend API Requests
                  FastAPI Service Layer
                           │
                           ▼
                  PostgreSQL Data Store
```

## Supported Integrations Matrix (Phase 2+)

1. **Gmail**:
   - Inbound email processing -> n8n webhook -> Classification -> Create Task / Notification.
2. **Google Calendar & Meet / Zoom**:
   - Meeting scheduled by AI Agent -> n8n trigger -> Create Calendar event & Video room link -> Store link in tasks or project metadata.
3. **Slack / Internal Messaging**:
   - Synchronize internal activity log notifications to Slack channels via n8n webhook.
