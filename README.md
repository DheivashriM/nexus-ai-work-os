# AI PM — Nexus AI Work Operating System Assistant

nexus-ai-work-os is an intelligent Project Management & Work Operating System assistant designed for engineering and product teams. It integrates natural language intent parsing, multi-turn tool execution, deterministic entity resolution, role-based access control (RBAC), and multi-provider LLM support.

---

## 🏛️ System Architecture Overview

The codebase is built on a clean 4-tier layer pattern separating agent orchestration, tool registries, provider factories, and persistence services:

```
                  ┌─────────────────────────────────┐
                  │    User Interface / Web Client  │
                  │        (Next.js / React)        │
                  └────────────────┬────────────────┘
                                   │  HTTP / REST API
                                   ▼
                  ┌─────────────────────────────────┐
                  │      FastAPI Gateway / Router   │
                  │   (/api/ai, /api/tasks, etc.)   │
                  └────────────────┬────────────────┘
                                   │
                                   ▼
                  ┌─────────────────────────────────┐
                  │     AI Agent Service / Engine   │  <--- (aiOrchestrator)
                  │      (Multi-Turn Loop)          │
                  └──────┬───────────────────┬──────┘
                         │                   │
                         ▼                   ▼
       ┌───────────────────────┐   ┌────────────────────────┐
       │   LLM Provider Factory│   │   Tools Registry Layer │  <--- (toolsRegistry)
       │(Gemini, OpenAI, Rule) │   │ (Function Definitions) │
       └───────────────────────┘   └─────────┬──────────────┘
                                             │
                                             ▼
                                   ┌───────────────────┐
                                   │   Safety Checker  │  <--- (RBAC Authorization)
                                   └─────────┬─────────┘
                                             │
                                             ▼
                                   ┌───────────────────┐
                                   │  Entity Resolver  │  <--- (entityResolver)
                                   └─────────┬─────────┘
                                             │
                                             ▼
                                   ┌───────────────────┐
                                   │  Domain Services  │
                                   │   (Task, Project) │
                                   └─────────┬─────────┘
                                             │
                                             ▼
                                   ┌───────────────────┐
                                   │    PostgreSQL /   │
                                   │  SQLite Database  │
                                   └───────────────────┘
```

### Core Architecture Modules

1. **AI Orchestrator** ([`agent_service.py`](file:///c:/pm%20tool/backend/app/agents/agent_service.py)): Manages multi-turn reasoning loops, context window history, and final response synthesis.
2. **LLM Provider Factory** ([`providers/`](file:///c:/pm%20tool/backend/app/agents/providers)): Instantiates LLM provider adapters (`OpenAIProvider`, `GeminiProvider`, `RuleBasedProvider`) based on environment configuration.
3. **Tools Registry** ([`registry.py`](file:///c:/pm%20tool/backend/app/tools/registry.py)): Central registry that converts tool definitions into OpenAI function schema and dispatches tool execution.
4. **RBAC & Safety Checker** ([`safety.py`](file:///c:/pm%20tool/backend/app/agents/safety.py)): Enforces user permissions and action risk categorization before executing any read/write tool.
5. **Entity Resolver** ([`entity_resolver.py`](file:///c:/pm%20tool/backend/app/tools/entity_resolver.py)): Resolves users, tasks, and projects deterministically by ID, exact name, email, or partial match without faking existence or guessing.

---

## ⚙️ Environment Configuration

Copy `.env.example` to `.env` in both root and backend directories before running:

```bash
cp .env.example .env
```

### Required Key Variables

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `DATABASE_URL` | SQLAlchemy DB Connection String | `sqlite:///./app.db` |
| `SECRET_KEY` | JWT Secret Key | `dev_secret_key_change_in_production` |
| `LLM_PROVIDER` / `VITE_LLM_PROVIDER` | LLM Provider (`rule_based`, `gemini`, `openai`) | `rule_based` |
| `GEMINI_API_KEY` / `VITE_GEMINI_API_KEY` | Google Gemini API Key | `AIzaSy...` |
| `OPENAI_API_KEY` | OpenAI API Key | `sk-...` |
| `LLM_MODEL` / `VITE_LLM_MODEL` | Preferred LLM Model Identifier | `gemini-1.5-pro` |

---

## 🚀 Running Locally

### 1. Backend (FastAPI Python)

Requirements: Python 3.10+

```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Backend API Documentation will be available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 2. Frontend (Next.js / React)

Requirements: Node.js 18+

```bash
cd frontend
npm install
npm run dev
```

Frontend interface will be available at: `http://localhost:3000`

---

## 🧪 Running Automated Tests

```bash
cd backend
pytest
```

All unit and integration tests covering AI Agent execution, entity resolution, task management, permissions, and webhooks must pass cleanly.

---

## 🚧 Known Limitations & In-Progress Work

- **Executive Mode & Action Follow-up Tracking**: In-progress feature designed for automated background monitoring of pending task commitments and blocker resolutions. Current architecture supports intent parsing and logging; background cron triggers are under active development.
- **pgvector RAG Integration**: Vector document search specification defined in [`docs/rag_architecture.md`](file:///c:/pm%20tool/docs/rag_architecture.md); planned for Phase 2 implementation.

---

## 📦 Suggested Git Commit for Fresh Repositories

When committing this codebase to a fresh git repository:

```bash
git init
git add .
git commit -m "feat(core): initial clean commit of Nexus AI Work Operating System

- Setup 4-tier AI Orchestrator, Tools Registry, Provider Factory, and Entity Resolver architecture
- Add support for Rule-Based, Gemini, and OpenAI LLM providers
- Include FastAPI backend, Next.js frontend, and unit test suite
- Add comprehensive handoff documentation and sanitized environment configuration"
```
