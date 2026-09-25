# Architecture Specification — AI Work Operating System

## System Overview

The AI Work Operating System is an intelligent startup management platform designed to unify project management, task execution, team workload tracking, operational audit logs, and internal messaging into a high-performance workspace.

```
Frontend (Next.js 14 + React + TypeScript + Tailwind CSS)
                       │
                       ▼  HTTP / REST JSON
Backend API (Python + FastAPI + Pydantic v2 + SQLAlchemy 2.0)
                       │
                       ▼
Database (PostgreSQL / Supabase / SQLite)
                       │
                       ├──────► Audit & Activity Logs
                       └──────► Internal Notifications

Future Integrations (Phase 2+)
                       │
                       ├──────► AI Agent & Tool Calling Architecture
                       ├──────► n8n Webhook & External Automations (Gmail, WhatsApp, Slack)
                       └──────► RAG Vector Engine (Documents & Knowledge Base)
```

## Architectural Design Principles

1. **Source of Truth Integrity**:
   - The PostgreSQL operational database is the single source of truth for live tasks, project statuses, team memberships, and audit trails.
   - LLMs and RAG engines are never treated as state storage; they consume and query structured APIs.

2. **Decoupled Layering**:
   - Route Handlers (`api/routes`) receive and validate payloads using Pydantic schemas.
   - Business Logic & Authorization (`services/`) enforces permissions, validates dependencies, creates audit activities, and triggers notifications.
   - Data Access Layer (`repositories/`) abstracts database CRUD operations using SQLAlchemy sessions.

3. **Strict Audit Trail**:
   - Every state mutation (task creation, assignment, status change, blocker filing, blocker resolution) automatically writes an entry to the `activities` table with metadata.

4. **AI Tool Boundaries**:
   - Future AI Agents connect to the platform strictly through validated service tools, passing through the identical permission checks as human users.
