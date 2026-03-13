# CNFund Documentation

_Last updated: 2026-03-13_

---

## Core Docs

| File | Description |
|------|-------------|
| [`project-overview-pdr.md`](./project-overview-pdr.md) | Product overview, business rules, fee logic, RBAC |
| [`codebase-summary.md`](./codebase-summary.md) | Directory structure, key files, module responsibilities |
| [`code-standards.md`](./code-standards.md) | Python + TypeScript conventions, API patterns |
| [`system-architecture.md`](./system-architecture.md) | Architecture diagrams, auth flow, API endpoint map, DB schema |
| [`project-roadmap.md`](./project-roadmap.md) | Security issues, technical debt, improvement priorities |
| [`deployment-guide.md`](./deployment-guide.md) | Railway + Vercel setup, env vars, backup, rollback |
| [`design-guidelines.md`](./design-guidelines.md) | Color system, typography, components, dark mode, PWA |

## Legacy Deploy Runbooks

| File | Description |
|------|-------------|
| [`DEPLOYMENT_LOW_COST_STABLE.md`](./DEPLOYMENT_LOW_COST_STABLE.md) | Detailed Railway + Vercel + PostgreSQL deploy runbook |
| [`CUTOVER_AND_ROLLBACK_PLAYBOOK.md`](./CUTOVER_AND_ROLLBACK_PLAYBOOK.md) | Release checklist + rollback playbook |

## Notes

- Streamlit UI và Supabase đã decommission — không còn được hỗ trợ.
- Runtime chính thức: Next.js frontend + FastAPI backend + PostgreSQL.
- Fund business data (`fund_*` tables) được quản lý bởi `core/postgres_data_handler.py`, tách biệt với auth tables (SQLAlchemy ORM).
