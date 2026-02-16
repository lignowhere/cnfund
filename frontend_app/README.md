# CNFund Frontend (Next.js)

Mobile-first frontend for CNFund strangler migration (replacing Streamlit UI gradually).

## Prerequisites

- Node.js 20+
- Backend API running at `http://localhost:8001`

## Install

```powershell
cd frontend_app
npm install
```

## Configure

Copy env file:

```powershell
Copy-Item .env.example .env.local
```

Default:

- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8001/api/v1`

## Run

```powershell
cd frontend_app
npm run dev
```

Open `http://localhost:3000`.

### One-command run (frontend + backend)

From repo root:

```powershell
npm run dev
```

Optional first run with dependency install:

```powershell
npm run dev:install
```

## Routes

- `/login`
- `/dashboard`
- `/transactions`
- `/investors`
- `/fees`
- `/reports`
- `/backup`

## Mobile UX hardening completed

- Fee apply requires preview token + dual safety acknowledgements.
- Backup restore requires explicit `RESTORE` confirmation phrase.
- Transactions/investors support paginated card list + `Load more`.
- Desktop table mode is controlled by backend feature flags.
- Full UI text now uses Vietnamese with dấu.
- Dashboard/Reports include visual charts (NAV trend, transaction mix, top investors).

## Quality checks

```powershell
cd frontend_app
npm run lint
npm run build
```

## Troubleshooting login `Failed to fetch`

- Ensure backend is running and reachable: `http://127.0.0.1:8001/health`.
- Ensure `frontend_app/.env.local` has correct `NEXT_PUBLIC_API_BASE_URL`.
- If frontend runs on another port (`3001`, `3002`), set backend CORS:
  - `API_ALLOWED_ORIGINS` for fixed domains
  - `API_ALLOWED_ORIGIN_REGEX` for local dynamic ports

## E2E (Playwright mobile matrix)

```powershell
cd frontend_app
npx playwright install
npm run test:e2e
```

Current suite:

- Android Chrome (Pixel 7)
- iOS Safari (iPhone 14)

## Production deployment recommendation

See `docs/DEPLOYMENT_LOW_COST_STABLE.md` for the final low-cost stable deployment blueprint and backup/restore policy.
